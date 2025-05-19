use std::fs::{File, remove_file};
use std::io::{Write, Read};
use std::process::Command;
use std::env::{temp_dir, current_dir};
use std::path::{Path, PathBuf}; // PathBuf est toujours importé, même si inutilisé ici.

// --- Structure pour la configuration reçue ---
#[derive(Debug, serde::Deserialize)]
struct AnonymizationConfig {
    #[serde(rename = "anonymizePersons")]
    anonymize_persons: bool,
    // Ajoutez d'autres options ici (anonymizeLocations, etc.)
}
// --------------------------------------------

#[tauri::command]
fn anonymize_text(input: String, config: AnonymizationConfig) -> Result<String, String> {
    let temp_dir = temp_dir();
    let input_path = temp_dir.join("anonyfiles_input.txt");
    let output_path = temp_dir.join("anonyfiles_output.txt");
    let error_output_path = temp_dir.join("anonyfiles_error_output.txt");

    // --- Afficher la configuration reçue pour débogage ---
    println!("DEBUG: Configuration reçue du frontend: {:?}", config);

    // Écrit le texte reçu dans le fichier d'entrée temporaire
    let mut input_file = File::create(&input_path).map_err(|e| format!("Erreur création fichier temporaire entrée: {:?}", e))?;
    input_file.write_all(input.as_bytes()).map_err(|e| format!("Erreur écriture fichier temporaire entrée: {:?}", e))?;
    let _ = input_file.flush();


    // --- Calcul du chemin cli_root ---
    let current_working_dir = current_dir()
        .map_err(|e| format!("Erreur lors de la détermination du répertoire de travail : {:?}", e))?;
    let cli_root_relative = current_working_dir.join("../../anonyfiles-cli");
    let absolute_cli_root = cli_root_relative.canonicalize()
        .map_err(|e| format!("Erreur lors de la canonicalisation du chemin CLI ({:?}): {:?}", cli_root_relative, e))?;

    // --- Les warnings de code mort ou de nommage seront corrigés plus tard si vous lancez 'cargo fix' ---
    // let cli_root_str = absolute_cli_root.to_str()
    //     .ok_or_else(|| "Chemin CLI canonicalisé invalide (non-UTF8)".to_string())?;


    // --- Début de la construction de la commande Python ---

    let main_py_path = absolute_cli_root.join("main.py");
    let python_executable = Path::new("python");

    // --- CORRECTION : Stocker le chemin du fichier de config dans une variable ---
    // Ceci est la correction pour l'erreur E0716. Cette variable doit vivre assez longtemps.
    let config_file_path = absolute_cli_root.join("generated_config.yaml"); // TODO: Remplacer par un fichier généré dynamiquement

    // --- CONSTRUCTION DYNAMIQUE DES ARGUMENTS DU CLI EN FONCTION DE LA CONFIG ---
    // On commence avec les arguments de base
    let mut command_args = vec![
        main_py_path.as_os_str(),
        "anonymize".as_ref(),
        input_path.as_os_str(),
        // Pour l'instant, on utilise toujours generated_config.yaml par défaut
        "--config".as_ref(),
        config_file_path.as_os_str(), // Utiliser la référence de la variable corrigée
        "-o".as_ref(),
        output_path.as_os_str(),
    ];

    // --- AJOUTE l'argument --exclude-entities PER si anonymize_persons est FALSE ---
    if !config.anonymize_persons {
        println!("DEBUG: Exclure les entités PER basé sur la config frontend.");
        // Note : Le CLI s'attend à --exclude-entities TYPE1 TYPE2 ...
        // Donc pour exclure un seul type, on ajoute deux arguments.
        command_args.push("--exclude-entities".as_ref());
        command_args.push("PER".as_ref());
    }


    // Afficher la commande complète qui va être exécutée
    println!("DEBUG: Commande Python complète (pour affichage): python {:?}", command_args);


    // Exécuter la commande Python
    let command_execution_result = Command::new(python_executable)
        .args(&command_args) // Passe les arguments dynamiquement construits
        .output();

    // Gérer le résultat de l'exécution (inchangé)
    match command_execution_result {
        Ok(output) => {
            println!("DEBUG: Sortie standard Python :\n{}", String::from_utf8_lossy(&output.stdout));
            println!("DEBUG: Erreur standard Python :\n{}", String::from_utf8_lossy(&output.stderr));

            if output.status.success() {
                let mut output_file = File::open(&output_path).map_err(|e| format!("Erreur lecture fichier sortie temporaire : {:?}", e))?;
                let mut output_text = String::new();
                output_file.read_to_string(&mut output_text).map_err(|e| format!("Erreur lecture fichier sortie temporaire : {:?}", e))?;

                // Nettoyage des fichiers temporaires
                let _ = remove_file(&input_path);
                let _ = remove_file(&output_path);
                let _ = remove_file(&error_output_path);

                Ok(output_text)
            } else {
                let error_message = if output.stderr.is_empty() {
                    format!("Le script Python a échoué (code {}). Sortie standard:\n{}", output.status.code().unwrap_or(-1), String::from_utf8_lossy(&output.stdout))
                } else {
                    format!("Le script Python a échoué (code {}). Erreur standard:\n{}", output.status.code().unwrap_or(-1), String::from_utf8_lossy(&output.stderr))
                };
                let _ = remove_file(&input_path);
                let _ = remove_file(&output_path);
                let _ = remove_file(&error_output_path);
                Err(error_message)
            }
        }
        Err(e) => {
            let _ = remove_file(&input_path);
            let _ = remove_file(&output_path);
            let _ = remove_file(&error_output_path);
            Err(format!("Erreur critique au lancement du processus Python par l'OS: {:?}", e))
        }
    }
}

// La fonction main reste inchangée
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![anonymize_text])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}