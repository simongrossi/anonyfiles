# 🦀 Source Code (Tauri/Rust)

Ce dossier contient le code Backend local de l'application GUI, développé en [Rust](https://www.rust-lang.org/) avec [Tauri](https://tauri.app/).

## 📂 Rôle

Il fait le pont entre l'interface web (Svelte) et le système d'exploitation. C'est ici que sont définies les commandes invoquées depuis le JS pour effectuer des actions système (lecture de fichiers, appel à python, etc.).

## 📄 Fichiers principaux

- **`main.rs`** : Point d'entrée de l'application Rust.
- **`tauri.conf.json`** : Configuration de Tauri (fenêtres, permissions, build).
- **`Cargo.toml`** : Dépendances Rust.
