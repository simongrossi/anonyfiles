#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::Manager;

#[tauri::command]
fn process_file(path: String) {
    println!("Processing file at path: {}", path);
    // Tu pourras ici appeler Python si nécessaire
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![process_file])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
