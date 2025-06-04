// #anonyfiles/anonyfiles_gui/src-tauri/src/presets.rs
use std::fs;
use std::path::PathBuf;
use tauri::api::path::resource_dir;
use tauri::{AppHandle, Runtime};

#[tauri::command]
pub async fn list_presets<R: Runtime>(app: AppHandle<R>) -> Result<Vec<String>, String> {
    // Récupère le chemin absolu vers le dossier presets situé dans public/
    let resource_base = app
        .path_resolver()
        .resolve_resource("../public/presets") // ✅ Correction ici
        .ok_or("Impossible de résoudre le dossier public/presets")?;

    let mut files = Vec::new();
    let entries = fs::read_dir(&resource_base).map_err(|e| format!("Erreur lecture dossier: {}", e))?;

    for entry in entries {
        let entry = entry.map_err(|e| e.to_string())?;
        let path = entry.path();
        if let Some(ext) = path.extension() {
            if ext == "json" {
                if let Some(file_name) = path.file_name().and_then(|n| n.to_str()) {
                    files.push(file_name.to_string());
                }
            }
        }
    }

    Ok(files)
}
