# 🦀 Shell natif Tauri 2 (Rust)

Code Rust qui sert d'environnement d'exécution à l'app desktop. Le rôle principal de ce shell est de **spawner l'API embarquée** (sidecar PyInstaller) et d'exposer son port au frontend Svelte.

## 📄 Fichiers principaux

- **`src/main.rs`** — entrée Rust. Enregistre les plugins (`tauri-plugin-shell`, `dialog`, `fs`, `clipboard-manager`), spawne le sidecar au démarrage sur un port libre (via `portpicker`), expose la commande `get_api_port` au frontend.
- **`src/presets.rs`** — commande `list_presets` qui énumère les fichiers JSON dans `public/presets/` (résolution via `BaseDirectory::Resource` en Tauri 2).
- **`Cargo.toml`** — deps : `tauri = "2"`, `tauri-plugin-shell`, `tauri-plugin-dialog`, `tauri-plugin-fs`, `tauri-plugin-clipboard-manager`, `portpicker`, `serde`, `serde_json`.
- **`tauri.conf.json`** — schéma Tauri 2. Le sidecar est distribué via `bundle.resources = ["sidecar/**/*"]` (dossier PyInstaller `--onedir` inclus tel quel).
- **`capabilities/default.json`** — permissions de la fenêtre `main` (`dialog:default`, `fs:default`, `clipboard-manager:default`). Pas besoin de `shell:allow-execute` : le sidecar est spawné depuis Rust, pas depuis le frontend.
- **`sidecar/anonyfiles-api/`** — dossier PyInstaller onedir (binaire + `_internal/`) produit par `make sidecar`. Non commité (voir `.gitignore`).

## 🔄 Cinématique au démarrage

```
Tauri.Builder::setup()
  ↓
portpicker::pick_unused_port()    → port libre (ex. 54321)
  ↓
app.path().resolve("sidecar/anonyfiles-api/anonyfiles-api[.exe]", BaseDirectory::Resource)
  ↓
app.shell().command(path).args(["--host","127.0.0.1","--port","54321"]).spawn()
  ↓
CommandChild stocké dans AppState (Mutex<Option<CommandChild>>)
  ↓
uvicorn démarre, répond à /api/health en ~1 s (warm) sur macOS
  ↓
frontend invoke('get_api_port') → 54321
  ↓
frontend fetch http://127.0.0.1:54321/api/... (HTTP standard)
```

À la fermeture (`WindowEvent::CloseRequested`) et à la sortie (`RunEvent::ExitRequested`), `main.rs` appelle explicitement `CommandChild::kill()` pour éviter tout zombie.

**Note cold start** : le premier lancement après installation sur macOS peut prendre 30-50 s à cause du scan Gatekeeper sur un bundle non signé. Les lancements suivants sont en ~1 s. Une signature Apple Developer ID + notarisation élimine ce délai.

## 🔧 Build local

```bash
# à la racine du repo
make sidecar         # produit binaries/anonyfiles-api-<triple>
cd anonyfiles_gui
npm run tauri dev    # ou `npm run tauri build` pour le release
```

Pour la CI multi-plateforme, voir [`.github/workflows/desktop-build.yml`](../../.github/workflows/desktop-build.yml).
