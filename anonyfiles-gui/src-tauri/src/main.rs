use std::fs::{File, remove_file};
use std::io::{Write, Read}; // Read is needed if you read the output file
use std::process::Command;
use std::env::{temp_dir, current_dir};
use std::path::{Path, PathBuf};

#[tauri::command]
fn anonymize_text(input: String) -> Result<String, String> {
    // Dossier temporaire
    let temp_dir = temp_dir();
    let input_path = temp_dir.join("anonyfiles_input.txt");
    let output_path = temp_dir.join("anonyfiles_output.txt");
    let error_output_path = temp_dir.join("anonyfiles_error_output.txt"); // Used for temporary error file if needed, but we'll return the string directly

    // Écrit le texte reçu dans le fichier d'entrée
    let mut input_file = File::create(&input_path).map_err(|e| format!("Erreur création fichier temporaire entrée: {:?}", e))?;
    input_file.write_all(input.as_bytes()).map_err(|e| format!("Erreur écriture fichier temporaire entrée: {:?}", e))?;
    let _ = input_file.flush(); // Ensure data is written to disk


    // --- Calcul du chemin cli_root et canonicalisation (inchangé) ---
    let current_working_dir = current_dir()
        .map_err(|e| format!("Erreur lors de la détermination du répertoire de travail : {:?}", e))?;

    let cli_root_relative = current_working_dir.join("../../anonyfiles-cli");

    let absolute_cli_root = cli_root_relative.canonicalize()
        .map_err(|e| format!("Erreur lors de la canonicalisation du chemin CLI ({:?}): {:?}", cli_root_relative, e))?;

    let cli_root_str = absolute_cli_root.to_str()
        .ok_or_else(|| "Chemin CLI canonicalisé invalide (non-UTF8)".to_string())?;

    // --- Prints de débogage (existants) ---
    println!("DEBUG: Répertoire de travail courant: {}", current_working_dir.display());
    println!("DEBUG: cli_root calculé (avant canonicalisation): {}", cli_root_relative.display());
    println!("DEBUG: cli_root canonicalisé: {}", absolute_cli_root.display());

    match std::env::var("PATH") {
        Ok(val) => println!("DEBUG: PATH dans l'application Tauri: {}", val),
        Err(e) => println!("DEBUG: PATH non trouvé : {:?}", e),
    }
    // --- Fin des prints de débogage ---


    // --- Début de la gestion robuste de l'exécution de commande Python ---

    // Chemin absolu vers le fichier de configuration YAML et le script main.py (utilisent le chemin canonicalisé)
    let config_path = absolute_cli_root.join("generated_config.yaml");
    let main_py_path = absolute_cli_root.join("main.py"); // Chemin vers main.py

    // Utiliser le nom de l'exécutable Python qui devrait être dans le PATH sur Windows
    let python_executable = Path::new("python"); // MODIFIÉ ICI POUR WINDOWS. Peut être "python3" selon votre install.


    // Construire la liste complète des arguments pour la commande Python
    let command_args = vec![
        main_py_path.as_os_str(), // Passer PathBuf/Path as OsStr for robustness
        "anonymize".as_ref(), // Arg simple
        input_path.as_os_str(), // Passer PathBuf
        "--config".as_ref(), // Option
        config_path.as_os_str(), // Passer PathBuf
        "-o".as_ref(), // Option
        output_path.as_os_str(), // Passer PathBuf
    ];

    // Afficher la commande complète qui va être exécutée (pour débogage)
    // Attention : afficher les OsStr peut donner des formats variés selon l'OS.
    // Pour un print lisible, reconstruire la chaîne comme avant :
    let debug_command_string = format!("{} {} anonymize {} --config {} -o {}",
        python_executable.display(),
        main_py_path.display(),
        input_path.display(),
        config_path.display(),
        output_path.display()
    );
    println!("DEBUG: Commande Python complète (pour affichage): {}", debug_command_string);


    // Exécuter la commande Python et capturer le résultat ou l'erreur de Lancement OS
    let command_execution_result = Command::new(python_executable)
        .args(&command_args) // Passe tous les arguments (OsStr)
        .output(); // Retourne un Result<Output, Error>

    // Gérer le résultat de l'exécution de la commande
    match command_execution_result {
        Ok(output) => { // La commande a été lancée avec succès par l'OS, maintenant vérifier le statut de sortie du processus Python
            // Print stdout/stderr au terminal pour débogage
            println!("DEBUG: Sortie standard Python :\n{}", String::from_utf8_lossy(&output.stdout));
            println!("DEBUG: Erreur standard Python :\n{}", String::from_utf8_lossy(&output.stderr));

            if output.status.success() {
                // Le script Python s'est terminé avec succès (code 0)
                // Lire le contenu du fichier de sortie temporaire
                let mut output_file = File::open(&output_path).map_err(|e| format!("Erreur lecture fichier sortie temporaire : {:?}", e))?;
                let mut output_text = String::new();
                output_file.read_to_string(&mut output_text).map_err(|e| format!("Erreur lecture fichier sortie temporaire : {:?}", e))?;

                // Nettoyage des fichiers temporaires
                let _ = remove_file(&input_path);
                let _ = remove_file(&output_path);
                let _ = remove_file(&error_output_path); // Clean up error file if created

                // Renvoyer le texte anonymisé au frontend
                Ok(output_text)
            } else {
                // Le script Python s'est terminé avec un code d'erreur non nul
                // Capturer et renvoyer stdout et stderr au frontend comme une erreur
                let error_message = if output.stderr.is_empty() {
                    // Si stderr est vide, renvoyer stdout (parfois le script met des messages d'erreur sur stdout)
                    format!("Le script Python a échoué (code {}). Sortie standard:\n{}", output.status.code().unwrap_or(-1), String::from_utf8_lossy(&output.stdout))
                } else {
                    // Sinon, renvoyer stderr
                    format!("Le script Python a échoué (code {}). Erreur standard:\n{}", output.status.code().unwrap_or(-1), String::from_utf8_lossy(&output.stderr))
                };

                // Nettoyage des fichiers temporaires
                let _ = remove_file(&input_path);
                let _ = remove_file(&output_path);
                 let _ = remove_file(&error_output_path); // Clean up error file if created

                // Renvoyer le message d'erreur au frontend via Result::Err
                Err(error_message)
            }
        }
        Err(e) => { // Erreur au lancement de la commande par l'OS (ex: exécutable introuvable)
            // Nettoyage des fichiers temporaires (s'ils ont été créés avant l'erreur de lancement)
            let _ = remove_file(&input_path);
            let _ = remove_file(&output_path);
             let _ = remove_file(&error_output_path); // Clean up error file if created

            // Renvoyer l'erreur de lancement de l'OS au frontend
            Err(format!("Erreur critique au lancement du processus Python: {:?}", e))
        }
    }
    // --- Fin de la gestion robuste de l'exécution de commande Python ---
}

// La fonction main reste inchangée
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![anonymize_text])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}