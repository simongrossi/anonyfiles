# ⚡ Commands

Ce dossier contient l'implémentation des différentes commandes disponibles dans le CLI Anonyfiles.

## 📂 Rôle

Chaque fichier correspond généralement à une sous-commande ou un groupe de fonctionnalités accessibles via `anonyfiles_cli <commande>`.

## 📄 Commandes

- **`anonymize.py`** : Logique de la commande d'anonymisation.
- **`deanonymize.py`** : Logique pour désanonymiser un fichier via un mapping.
- **`config.py`** : Gestion de la configuration (création, validation).
- **`batch.py`** : Traitement par lots de dossiers.
- **`clean_job.py`** : Nettoyage des fichiers temporaires et jobs.
