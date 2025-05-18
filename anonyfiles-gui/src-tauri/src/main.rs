use std::fs::{File, remove_file};
use std::io::{Write, Read}; // Keep Read if reading output
use std::process::Command;
use std::env::{temp_dir, current_dir};
use std::path::{Path, PathBuf}; // Keep Path and PathBuf

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

    // --- Calcul du chemin cli_root et canonicalisation (inchangé) ---
    let current_working_dir = current_dir()
        .map_err(|e| format!("Erreur lors de la détermination du répertoire de travail : {:?}", e))?;

    let cli_root_relative = current_working_dir.join("../../anonyfiles-cli");

    let absolute_cli_root = cli_root_relative.canonicalize()
        .map_err(|e| format!("Erreur lors de la canonicalisation du chemin CLI ({:?}): {:?}", cli_root_relative, e))?;

    // --- Prints de débogage (existants) ---
    println!("DEBUG: Répertoire de travail courant: {}", current_working_dir.display());
    println!("DEBUG: cli_root calculé (avant canonicalisation): {}", cli_root_relative.display());
    println!("DEBUG: cli_root canonicalisé: {}", absolute_cli_root.display());

    match std::env::var("PATH") {
        Ok(val) => println!("DEBUG: PATH dans l'application Tauri: {}", val),
        Err(e) => println!("DEBUG: PATH non trouvé : {:?}", e),
    }
    // --- Fin des prints de débogage ---


    // --- Début de la MODIFICATION : Construire les PathBuf et les passer directement à Command ---
    // Chemins absolus vers les fichiers (utilisent le chemin canonicalisé)
    let config_path_buf = absolute_cli_root.join("generated_config.yaml");
    let main_py_path_buf = absolute_cli_root.join("main.py"); // Chemin vers main.py

    // Utiliser le chemin explicite de l'exécutable Python
    let python_executable = Path::new("/Library/Frameworks/Python.framework/Versions/3.11/bin/python3"); // Utilise Path::new pour l'exécutable


    // Construire la commande complète pour le débogage (en utilisant les chemins canoniques)
    // Utiliser display() pour les PathBuf pour les prints de débogage
    let command_debug_string = format!("{} {} anonymize {} --config {} -o {}",
        python_executable.display(),
        main_py_path_buf.display(),
        input_path.display(),
        config_path_buf.display(),
        output_path.display()
    );
    println!("DEBUG: Commande Python complète: {}", command_debug_string);
    // --- Fin de la MODIFICATION ---


    // Commande Python à exécuter (PASSER LES PathBuf DIRECTEMENT autant que possible)
    let output = Command::new(python_executable) // Utilise Path pour l'exécutable
        .arg(&main_py_path_buf) // Passer PathBuf directement
        .arg("anonymize")
        .arg(&input_path) // Passer PathBuf directement
        .arg("--config")
        .arg(&config_path_buf) // Passer PathBuf directement
        .arg("-o")
        .arg(&output_path) // Passer PathBuf directement
        .output()
        .map_err(|e| format!("Erreur lancement Python: {:?}", e))?; // Capture l'erreur de lancement au niveau OS

    // ... rest of the code for checking success, reading output, cleaning up ...
     if !output.status.success() {
        let error_message = if output.stderr.is_empty() {
             format!("Le script Python a échoué. Sortie standard:\n{}", String::from_utf8_lossy(&output.stdout))
        } else {
             format!("Le script Python a échoué. Erreur standard:\n{}", String::from_utf8_lossy(&output.stderr))
        };

        let _ = remove_file(&input_path);
        let _ = remove_file(&output_path);
        let _ = remove_file(&error_output_path);

        return Err(error_message);
    }

    let mut output_file = File::open(&output_path).map_err(|e| e.to_string())?;
    let mut output_text = String::new();
    output_file.read_to_string(&mut output_text).map_err(|e| e.to_string())?;

    let _ = remove_file(&input_path);
    let _ = remove_file(&output_path);
    let _ = remove_file(&error_output_path);

    Ok(output_text)
}

// main function remains unchanged
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![anonymize_text])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}