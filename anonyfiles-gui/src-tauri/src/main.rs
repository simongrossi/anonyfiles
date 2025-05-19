use std::fs::{File, remove_file};
use std::io::{Write, Read};
use std::process::Command;
use std::env::current_dir;
use std::path::{Path, PathBuf};

#[derive(Debug, serde::Deserialize)]
struct AnonymizationConfig {
    #[serde(rename = "anonymizePersons")]
    anonymize_persons: bool,
    // Ajoutez d'autres options ici si besoin
}

#[tauri::command]
fn anonymize_text(input: String, config: AnonymizationConfig) -> Result<String, String> {
    // Chemin dynamique : on remonte d'un niveau depuis anonyfiles-gui, puis anonyfiles-cli
    let project_root = current_dir()
        .map_err(|e| format!("Erreur accès current_dir : {:?}", e))?;

    // Vérifie si on est dans anonyfiles-gui ou dans anonyfiles-gui/src-tauri
    // (la racine du projet ou src-tauri, les 2 cas courants)
    let gui_root = if project_root.ends_with("src-tauri") {
        project_root.parent().unwrap().to_path_buf()
    } else {
        project_root
    };

    let cli_dir = gui_root.parent()
        .map(|p| p.join("anonyfiles-cli"))
        .ok_or("Impossible de déterminer le chemin du dossier anonyfiles-cli")?;

    // Dossier d'outputs à la racine du GUI (propre)
    let temp_dir = gui_root.join("anonyfiles_outputs");
    std::fs::create_dir_all(&temp_dir)
        .map_err(|e| format!("Erreur création dossier anonyfiles_outputs : {:?}", e))?;

    let input_path = temp_dir.join("anonyfiles_input.txt");
    let output_path = temp_dir.join("anonyfiles_output.txt");
    let error_output_path = temp_dir.join("anonyfiles_error_output.txt");

    println!("DEBUG: Tous les fichiers temporaires dans {:?}", temp_dir);

    // --- Afficher la configuration reçue pour débogage ---
    println!("DEBUG: Configuration reçue du frontend: {:?}", config);

    // Écrit le texte reçu dans le fichier d'entrée temporaire
    let mut input_file = File::create(&input_path).map_err(|e| format!("Erreur création fichier temporaire entrée: {:?}", e))?;
    input_file.write_all(input.as_bytes()).map_err(|e| format!("Erreur écriture fichier temporaire entrée: {:?}", e))?;
    let _ = input_file.flush();

    // CHEMIN VERS main.py et generated_config.yaml (dynamique)
    let main_py_path = cli_dir.join("main.py");
    let python_executable = Path::new("python");
    let config_file_path = cli_dir.join("generated_config.yaml");
    let output_dir = &temp_dir;

    // Vérification existence CLI
    if !main_py_path.exists() {
        return Err(format!("main.py introuvable à cet emplacement : {:?}", main_py_path));
    }
    if !config_file_path.exists() {
        return Err(format!("generated_config.yaml introuvable à cet emplacement : {:?}", config_file_path));
    }

    // Construction des arguments de la commande
    let mut command_args = vec![
        main_py_path.to_str().unwrap(),
        "anonymize",
        input_path.to_str().unwrap(),
        "--config",
        config_file_path.to_str().unwrap(),
        "-o",
        output_path.to_str().unwrap(),
        "--output-dir",
        output_dir.to_str().unwrap(),
    ];

    if !config.anonymize_persons {
        println!("DEBUG: Exclure les entités PER basé sur la config frontend.");
        command_args.push("--exclude-entities");
        command_args.push("PER");
    }

    println!("DEBUG: Commande Python complète (pour affichage): python {:?}", command_args);

    let command_execution_result = Command::new(python_executable)
        .args(&command_args)
        .output();

    match command_execution_result {
        Ok(output) => {
            println!("DEBUG: Sortie standard Python :\n{}", String::from_utf8_lossy(&output.stdout));
            println!("DEBUG: Erreur standard Python :\n{}", String::from_utf8_lossy(&output.stderr));

            if output.status.success() {
                let mut output_file = File::open(&output_path).map_err(|e| format!("Erreur lecture fichier sortie temporaire : {:?}", e))?;
                let mut output_text = String::new();
                output_file.read_to_string(&mut output_text).map_err(|e| format!("Erreur lecture fichier sortie temporaire : {:?}", e))?;

                // Nettoyage
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

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![anonymize_text])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
