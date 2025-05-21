# 🧩 anonyfiles_api

API FastAPI pour le projet [anonyfiles](https://github.com/simongrossi/anonyfiles)

---

## 🚀 Fonctionnalités principales

- API REST pour anonymiser et désanonymiser des fichiers textes, tableurs ou documents Office
- Basée sur [FastAPI](https://fastapi.tiangolo.com/)
- Utilise le moteur d’anonymisation situé dans le dossier `anonymizer/`

---

## 🛠️ Prérequis

- Python 3.10 ou 3.11 recommandé
- [pip](https://pip.pypa.io/)
- Dépendances listées dans `requirements.txt` (à la racine du projet ou dans ce dossier)

---

## ⚡ Installation

Depuis le dossier racine du projet :

```bash
cd anonyfiles_api
pip install -r ../requirements.txt
```

Ou, si vous utilisez un `requirements.txt` local :

```bash
pip install -r requirements.txt
```

---

## 🏃‍♂️ Lancement du serveur de développement

Depuis la racine du projet :

```bash
uvicorn anonyfiles_api.api:app --reload --host 0.0.0.0 --port 8000
```

Sous Windows (si les imports échouent) :

```cmd
set PYTHONPATH=.
uvicorn anonyfiles_api.api:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔗 Endpoints principaux

| Méthode | Endpoint       | Description                             |
|---------|----------------|-----------------------------------------|
| POST    | `/anonymize`   | Anonymise un texte ou un fichier        |
| POST    | `/deanonymize` | Désanonymise un texte via un mapping    |
| GET     | `/health`      | Vérifie le bon fonctionnement du serveur |

➡️ Voir la documentation interactive : http://localhost:8000/docs

---

## 🏗️ Structure du dossier

```bash
anonyfiles_api/
│
├── api.py           # Point d'entrée FastAPI
├── routes/          # (optionnel) fichiers pour séparer les endpoints
├── models/          # (optionnel) schémas Pydantic
├── ...
```

---

## 💡 Conseils

- Toujours exécuter le serveur depuis la racine du projet pour garantir la résolution correcte des imports.
- Pour un déploiement en production, privilégier Gunicorn/Uvicorn avec Nginx, ou un service cloud adapté.

---

## 📚 Ressources utiles

- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Projet anonyfiles sur GitHub](https://github.com/simongrossi/anonyfiles)

---

## 👤 Auteur principal

Simon Grossi