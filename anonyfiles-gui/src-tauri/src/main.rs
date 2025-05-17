use std::fs::{File, remove_file};
use std::io::{Write, Read};
use std::process::Command;
use std::env::temp_dir;

#[tauri::command]
fn anonymize_text(input: String) -> Result<String, String> {
    // Dossier temporaire
    let temp_dir = temp_dir();
    let input_path = temp_dir.join("anonyfiles_input.txt");
    let output_path = temp_dir.join("anonyfiles_output.txt");

    // Écrit le texte reçu dans le fichier d'entrée
    let mut input_file = File::create(&input_path).map_err(|e| e.to_string())?;
    input_file.write_all(input.as_bytes()).map_err(|e| e.to_string())?;

    // Chemin absolu vers le dossier CLI anonyfiles-cli
    // <--- MODIFIE CE CHEMIN SELON TON ARBORESCENCE --->
    let cli_root = r"C:\Users\simongrossi\Documents\GitHub\anonyfiles\anonyfiles-cli";

    // Chemin absolu vers le fichier de configuration YAML
    let config_path = format!("{}\\generated_config.yaml", cli_root);

    // Commande Python à exécuter
    let status = Command::new("python")
        .arg(format!("{}/main.py", cli_root))
        .arg("anonymize")
        .arg(input_path.to_str().unwrap())
        .arg("--config")
        .arg(&config_path)
        .arg("-o")
        .arg(output_path.to_str().unwrap())
        .status()
        .map_err(|e| format!("Erreur lancement Python: {:?}", e))?;

    if !status.success() {
        return Err("Le script Python a échoué".to_string());
    }

    // Lit le résultat dans le fichier de sortie
    let mut output_file = File::open(&output_path).map_err(|e| e.to_string())?;
    let mut output_text = String::new();
    output_file.read_to_string(&mut output_text).map_err(|e| e.to_string())?;

    // Nettoyage fichiers temporaires
    let _ = remove_file(&input_path);
    let _ = remove_file(&output_path);

    Ok(output_text)
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![anonymize_text])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
