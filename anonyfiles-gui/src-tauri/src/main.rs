use std::fs::{File, remove_file};
use std::io::{Write, Read}; // Read est toujours nécessaire si vous lisez le fichier de sortie
use std::process::Command;
use std::env::{temp_dir, current_dir};
use std::path::PathBuf;

#[tauri::command]
fn anonymize_text(input: String) -> Result<String, String> {
    // Dossier temporaire
    let temp_dir = temp_dir();
    let input_path = temp_dir.join("anonyfiles_input.txt");
    let output_path = temp_dir.join("anonyfiles_output.txt");
    let error_output_path = temp_dir.join("anonyfiles_error_output.txt");

    // Écrit le texte reçu dans le fichier d'entrée
    let mut input_file = File::create(&input_path).map_err(|e| e.to_string())?;
    input_file.write_all(input.as_bytes()).map_err(|e| e.to_string())?;

    // --- Début du calcul du chemin cli_root (inchangé) ---
    let current_working_dir = current_dir()
        .map_err(|e| format!("Erreur lors de la détermination du répertoire de travail : {:?}", e))?;

    let cli_root_relative = current_working_dir.join("../../anonyfiles-cli");

    let absolute_cli_root = cli_root_relative.canonicalize()
        .map_err(|e| format!("Erreur lors de la canonicalisation du chemin CLI ({:?}): {:?}", cli_root_relative, e))?;

    let cli_root_str = absolute_cli_root.to_str()
        .ok_or_else(|| "Chemin CLI canonicalisé invalide (non-UTF8)".to_string())?;
    // --- Fin du calcul du chemin cli_root ---


    // --- Prints de débogage (existants) ---
    println!("DEBUG: Répertoire de travail courant: {}", current_working_dir.display());
    println!("DEBUG: cli_root calculé (avant canonicalisation): {}", cli_root_relative.display());
    println!("DEBUG: cli_root canonicalisé: {}", absolute_cli_root.display());

    match std::env::var("PATH") {
        Ok(val) => println!("DEBUG: PATH dans l'application Tauri: {}", val),
        Err(e) => println!("DEBUG: PATH non trouvé : {:?}", e),
    }
    // --- Fin des prints de débogage ---


    // Chemin absolu vers le fichier de configuration YAML et le script main.py (utilisent le chemin canonicalisé)
    let config_path = absolute_cli_root.join("generated_config.yaml");
    let main_py_path = absolute_cli_root.join("main.py"); // Chemin vers main.py

    // --- Début du code d'exécution Python (réactivé) ---
    // Utiliser le chemin explicite de l'exécutable Python
    let python_executable = "/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"; // CONFIRMEZ QUE PYTHON3 EST ICI

    // Construire la liste complète des arguments pour la commande Python
    let command_args = vec![
        main_py_path.to_str().unwrap(), // Le chemin vers main.py (canonicalisé)
        "anonymize", // L'argument 'anonymize' pour typer
        input_path.to_str().unwrap(), // Chemin du fichier d'entrée temporaire
        "--config", // Option '--config'
        config_path.to_str().unwrap(), // Chemin du fichier de config YAML (canonicalisé)
        "-o", // Option '-o' pour le fichier de sortie
        output_path.to_str().unwrap(), // Chemin du fichier de sortie temporaire
    ];

    // Afficher la commande complète qui va être exécutée (avec les chemins canonicalisés)
    println!("DEBUG: Commande Python complète: {} {}", python_executable, command_args.join(" "));


    // Commande Python à exécuter
    let output = Command::new(python_executable) // Utilise le chemin explicite vers l'exécutable python
        .args(&command_args) // Passe tous les arguments construits
        .output()
        .map_err(|e| format!("Erreur lancement Python: {:?}", e))?; // Capture l'erreur de lancement au niveau OS

    // Check if the command was successful
    if !output.status.success() {
        // Capture et renvoie stderr si la commande a échoué
        let error_message = if output.stderr.is_empty() {
             format!("Le script Python a échoué. Sortie standard:\n{}", String::from_utf8_lossy(&output.stdout))
        } else {
             format!("Le script Python a échoué. Erreur standard:\n{}", String::from_utf8_lossy(&output.stderr))
        };

        let _ = remove_file(&input_path);
        let _ = remove_file(&output_path);
        let _ = remove_file(&error_output_path); // Clean up the error file if it was created

        return Err(error_message); // Renvoie l'erreur
    }

    // Lit le résultat dans le fichier de sortie
    let mut output_file = File::open(&output_path).map_err(|e| e.to_string())?;
    let mut output_text = String::new();
    output_file.read_to_string(&mut output_text).map_err(|e| e.to_string())?;

    // Nettoyage fichiers temporaires
    let _ = remove_file(&input_path);
    let _ = remove_file(&output_path);
    let _ = remove_file(&error_output_path);

    Ok(output_text)
    // --- Fin du code d'exécution Python (réactivé) ---
}

// Le reste du code (fonction main) reste inchangé.
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![anonymize_text])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}