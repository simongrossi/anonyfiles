# 🧩 anonyfiles_api

API FastAPI pour le projet [anonyfiles](https://github.com/simongrossi/anonyfiles)

---

## 🚀 Fonctionnalités principales

- API REST pour anonymiser et désanonymiser des fichiers textes, tableurs ou documents Office
- Basée sur [FastAPI](https://fastapi.tiangolo.com/)
- Utilise le moteur d’anonymisation situé dans le dossier `anonymizer/`
- Traitement asynchrone avec suivi par `job_id`

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

| Méthode | Endpoint                  | Description                                |
|---------|---------------------------|--------------------------------------------|
| POST    | `/anonymize`              | Anonymise un texte ou un fichier (async)   |
| GET     | `/anonymize_status/{id}`  | Vérifie le statut d’un job d’anonymisation |
| POST    | `/deanonymize`            | Désanonymise un texte via un mapping       |
| GET     | `/health`                 | Vérifie le bon fonctionnement du serveur   |

➡️ Voir la documentation interactive : http://localhost:8000/docs

---

## 🔄 API Anonyfiles - Asynchrone

Cette API permet d’anonymiser des fichiers via un traitement asynchrone.

### POST `/anonymize/`

- Lance un job d’anonymisation en arrière-plan.
- Paramètres :
  - `file`: fichier à anonymiser (upload multipart/form-data)
  - `config_options`: JSON string des options d’anonymisation (ex: entités à exclure, règles personnalisées)
  - `file_type` *(optionnel)*
  - `has_header` *(optionnel)*

- Exemple de réponse :

```json
{
  "job_id": "uuid-unique-du-job",
  "status": "pending"
}
```

### GET `/anonymize_status/{job_id}`

- Permet de vérifier le statut du job.
- Retourne :
  - `pending` : en cours
  - `finished` : terminé
  - `error` : erreur lors du traitement

#### Exemple de réponse (job terminé) :

```json
{
  "status": "finished",
  "anonymized_text": "...texte anonymisé...",
  "audit_log": [
    {
      "pattern": "Jean Dupont",
      "replacement": "NOM001",
      "type": "spacy",
      "count": 1
    }
  ]
}
```

🧹 Les fichiers temporaires sont nettoyés automatiquement.  
🌐 CORS activé pour permettre les appels depuis le frontend.  
🔐 Utilise un UUID unique par job pour isoler les traitements.

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
