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

Les dépendances Python sont centralisées à la racine du dépôt :

- `pyproject.toml` est la source de vérité et déclare Python 3.11+.
- `requirements.txt` est le lock runtime généré depuis `pyproject.toml` avec `pip-tools`.

Installez le moteur depuis la racine avec `python -m pip install .`, puis
téléchargez le modèle NLP avec `python -m spacy download fr_core_news_md`.
