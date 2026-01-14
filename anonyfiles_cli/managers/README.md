# 👔 Managers

Ce dossier regroupe les classes de gestion "métier" utilitaires pour la CLI.

## 📂 Rôle

Il centralise la logique de validation, de gestion des chemins et de fusion des configurations.

## 📄 Fichiers principaux

- **`config_manager.py`** : Fusionne la configuration par défaut, locale et les arguments CLI.
- **`path_manager.py`** : Résout les chemins système et les dossiers de sortie.
- **`validation_manager.py`** : Valide les fichiers de config YAML (via Cerberus).
