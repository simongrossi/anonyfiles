# 🧠 anonyfiles_core

`anonyfiles_core` contient la logique principale d'anonymisation et de désanonymisation utilisée par l'ensemble du projet. Cette bibliothèque est indépendante et peut être installée seule pour être réutilisée dans d'autres applications.

Elle est appelée directement par:
- `anonyfiles_cli` pour les traitements en ligne de commande.
- `anonyfiles_api` pour exposer ces traitements via HTTP.

## 📂 Contenu du dossier

- **`anonymizer/`** : Contient le moteur d'anonymisation (logique de remplacement, NLP avec spaCy, règles regex).
- **`config/`** : Gestion de la configuration et schémas de validation.
- **`__init__.py`** : Fichier d'initialisation du package.

## 📦 Dépendances

Chaque module possède son fichier `requirements.txt` afin de permettre une installation séparée selon vos besoins.
Les dépendances principales incluent `spacy`, `faker`, et `pyyaml`.
