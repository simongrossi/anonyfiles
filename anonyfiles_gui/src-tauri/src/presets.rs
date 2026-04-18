use std::fs;

use tauri::path::BaseDirectory;
use tauri::{AppHandle, Manager, Runtime};

#[tauri::command]
pub async fn list_presets<R: Runtime>(app: AppHandle<R>) -> Result<Vec<String>, String> {
    let resource_base = app
        .path()
        .resolve("public/presets", BaseDirectory::Resource)
        .map_err(|e| format!("Impossible de résoudre le dossier public/presets : {}", e))?;

    let entries = fs::read_dir(&resource_base)
        .map_err(|e| format!("Erreur lecture dossier: {}", e))?;

    let mut files = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if path.extension().and_then(|e| e.to_str()) == Some("json") {
            if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
                files.push(file_name.to_string());
            }
        }
    }

    Ok(files)
}
