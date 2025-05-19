use std::fs::{File, remove_file};
use std::io::{Write, Read};
use std::process::Command;
use std::env::current_dir;
use std::path::{Path, PathBuf};

#[derive(Debug, serde::Deserialize)]
struct AnonymizationConfig {
    #[serde(rename = "anonymizePersons")]
    anonymize_persons: bool,
    #[serde(rename = "anonymizeLocations")]
    anonymize_locations: bool,
    #[serde(rename = "anonymizeOrgs")]
    anonymize_orgs: bool,
    #[serde(rename = "anonymizeEmails")]
    anonymize_emails: bool,
    #[serde(rename = "anonymizeDates")]
    anonymize_dates: bool,
    // Ajoute d’autres options ici si besoin
}

#[tauri::command]
fn anonymize_text(
    input: String,
    config: AnonymizationConfig,
    file_type: Option<String>,    // "csv", "xlsx", "txt" si fourni
    has_header: Option<bool>      // true/false si fourni
) -> Result<String, String> {
    // Chemin dynamique : on remonte d'un niveau depuis anonyfiles-gui, puis anonyfiles-cli
    let project_root = current_dir()
        .map_err(|e| format!("Erreur accès current_dir : {:?}", e))?;

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
    println!("DEBUG: Configuration reçue du frontend: {:?}", config);
    println!("DEBUG: file_type reçu : {:?}", file_type);
    println!("DEBUG: has_header reçu : {:?}", has_header);

    // Écrit le texte reçu dans le fichier d'entrée temporaire
    let mut input_file = File::create(&input_path).map_err(|e| format!("Erreur création fichier temporaire entrée: {:?}", e))?;
    input_file.write_all(input.as_bytes()).map_err(|e| format!("Erreur écriture fichier temporaire entrée: {:?}", e))?;
    let _ = input_file.flush();

    // Chemin vers main.py et generated_config.yaml (dynamique)
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

    // Construction des arguments de la commande (tout en String)
    let mut command_args: Vec<String> = vec![
        main_py_path.to_str().unwrap().to_string(),
        "anonymize".into(),
        input_path.to_str().unwrap().to_string(),
        "--config".into(),
        config_file_path.to_str().unwrap().to_string(),
        "-o".into(),
        output_path.to_str().unwrap().to_string(),
        "--output-dir".into(),
        output_dir.to_str().unwrap().to_string(),
    ];

    // Détection des entités à exclure selon config
    let mut exclude_entities = Vec::new();
    if !config.anonymize_persons {
        exclude_entities.push("PER");
    }
    if !config.anonymize_locations {
        exclude_entities.push("LOC");
    }
    if !config.anonymize_orgs {
        exclude_entities.push("ORG");
    }
    if !config.anonymize_emails {
        exclude_entities.push("EMAIL");
    }
    if !config.anonymize_dates {
        exclude_entities.push("DATE");
    }
    // Ajoute ici tes autres options si besoin

    if !exclude_entities.is_empty() {
        command_args.push("--exclude-entities".into());
        command_args.push(exclude_entities.join(","));
    }

    // Ajout paramètre --has-header si pertinent (uniquement csv/xlsx)
    if let Some(file_type) = &file_type {
        if file_type == "csv" || file_type == "xlsx" {
            if let Some(has_header) = has_header {
                command_args.push("--has-header".into());
                command_args.push(if has_header { "true".into() } else { "false".into() });
            }
        }
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
