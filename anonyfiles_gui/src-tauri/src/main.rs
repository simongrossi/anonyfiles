mod presets;

use std::sync::Mutex;

use presets::list_presets;
use tauri::path::BaseDirectory;
use tauri::{Manager, RunEvent, State, WindowEvent};
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

struct ApiPort(u16);

struct SidecarChild(Mutex<Option<CommandChild>>);

#[tauri::command]
fn get_api_port(state: State<'_, ApiPort>) -> u16 {
    state.0
}

fn sidecar_binary_name() -> &'static str {
    if cfg!(windows) {
        "anonyfiles-api.exe"
    } else {
        "anonyfiles-api"
    }
}

fn main() {
    let context = tauri::generate_context!();

    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .setup(|app| {
            let port = portpicker::pick_unused_port().expect("no free TCP port available");
            app.manage(ApiPort(port));
            app.manage(SidecarChild(Mutex::new(None)));

            let binary_name = sidecar_binary_name();
            let resource_rel = format!("sidecar/anonyfiles-api/{}", binary_name);
            let binary_path = app
                .path()
                .resolve(&resource_rel, BaseDirectory::Resource)
                .unwrap_or_else(|e| {
                    panic!("failed to resolve sidecar resource {resource_rel}: {e}")
                });

            let binary_str = binary_path.to_string_lossy().to_string();
            eprintln!("[setup] spawning sidecar: {binary_str}");

            // Le sidecar hérite du CWD de l'app (souvent "/" quand lancée depuis
            // Finder). On lui fournit un dossier jobs/ écrivable dans le user
            // data dir pour éviter le crash "Read-only file system".
            let jobs_dir = app
                .path()
                .app_data_dir()
                .map(|d| d.join("jobs"))
                .unwrap_or_else(|_| std::env::temp_dir().join("anonyfiles-jobs"));
            let _ = std::fs::create_dir_all(&jobs_dir);
            eprintln!("[setup] jobs dir: {}", jobs_dir.display());

            let (mut rx, child) = app
                .shell()
                .command(&binary_str)
                .env("ANONYFILES_JOBS_DIR", jobs_dir.to_string_lossy().to_string())
                .args([
                    "--host",
                    "127.0.0.1",
                    "--port",
                    &port.to_string(),
                ])
                .spawn()
                .unwrap_or_else(|e| panic!("failed to spawn sidecar {binary_str}: {e}"));

            {
                let handle: State<SidecarChild> = app.state();
                *handle.0.lock().unwrap() = Some(child);
            }

            tauri::async_runtime::spawn(async move {
                while let Some(event) = rx.recv().await {
                    match event {
                        CommandEvent::Stdout(line) => {
                            println!("[sidecar] {}", String::from_utf8_lossy(&line));
                        }
                        CommandEvent::Stderr(line) => {
                            eprintln!("[sidecar] {}", String::from_utf8_lossy(&line));
                        }
                        CommandEvent::Terminated(payload) => {
                            eprintln!("[sidecar] terminated: {payload:?}");
                            break;
                        }
                        _ => {}
                    }
                }
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::CloseRequested { .. }) {
                if let Some(state) = window.try_state::<SidecarChild>() {
                    if let Some(child) = state.0.lock().unwrap().take() {
                        let _ = child.kill();
                    }
                }
            }
        })
        .invoke_handler(tauri::generate_handler![get_api_port, list_presets])
        .build(context)
        .expect("error while building tauri application")
        .run(|app, event| {
            if let RunEvent::ExitRequested { .. } = event {
                if let Some(state) = app.try_state::<SidecarChild>() {
                    if let Some(child) = state.0.lock().unwrap().take() {
                        let _ = child.kill();
                    }
                }
            }
        });
}
