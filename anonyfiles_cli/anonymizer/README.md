# 🕵️ Anonymizer Wrapper (CLI)

Ce dossier contient la couche d'adaptation du moteur d'anonymisation pour l'interface en ligne de commande (CLI).

## 📂 Rôle

Il fait le lien entre les commandes utilisateur et le noyau `anonyfiles_core`. Il gère l'instanciation du moteur avec les configurations spécifiques à la CLI (barres de progression, affichage console).

## 📄 Fichiers principaux

- **`anonyfiles_core.py`** : Point d'entrée principal pour l'exécution depuis la CLI.
- **`*_processor.py`** : Logique de traitement spécifique par format de fichier.
- **`audit.py`** : Génération des rapports d'audit.
