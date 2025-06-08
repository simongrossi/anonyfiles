
# 🧩 anonyfiles_api

API [FastAPI](https://fastapi.tiangolo.com/) pour le projet [anonyfiles](https://github.com/simongrossi/anonyfiles)
reposant sur le moteur commun `anonyfiles_core`. L’API expose ainsi les mêmes
Ce projet est structuré en trois couches : `anonyfiles_core`, `anonyfiles_cli` et `anonyfiles_api`.
fonctionnalités que la CLI mais via des endpoints REST.

---

## 🚀 Fonctionnalités principales

- API REST pour **anonymiser** et **désanonymiser** des fichiers texte, tableurs ou documents bureautiques (.txt, .csv, .docx, .xlsx, .json, .pdf)
- Basée sur FastAPI avec documentation Swagger intégrée
- Utilise le moteur d’anonymisation du dossier `anonymizer/`
- Traitement **asynchrone** avec suivi par `job_id`
- Nettoyage automatique des fichiers temporaires
- CORS activé pour utilisation avec le frontend GUI

---

## 🛠️ Prérequis

- Python 3.10 ou 3.11 recommandé
- [pip](https://pip.pypa.io/)
- Dépendances listées dans `requirements.txt` (racine du projet ou local)

---

## ⚡ Installation

Depuis la racine du projet :

```bash
cd anonyfiles_api
pip install -r ../requirements.txt
```

Ou installation indépendante :

```bash
pip install -r requirements.txt  # installe également anonyfiles_core
```

---

## 🏃‍♂️ Lancement du serveur de développement

```bash
uvicorn anonyfiles_api.api:app --reload --host 0.0.0.0 --port 8000
```

Sous Windows (si les imports échouent) :

```dos
pip install -e .
uvicorn anonyfiles_api.api:app --reload --host 0.0.0.0 --port 8000
```

---

## 🔗 Endpoints principaux

| Méthode | Endpoint                     | Description                                      |
|---------|------------------------------|--------------------------------------------------|
| POST    | `/anonymize`                 | Anonymise un fichier ou texte (asynchrone)       |
| GET     | `/anonymize_status/{job_id}` | Vérifie le statut d’un job                       |
| WS      | `/ws/{job_id}`               | Statut temps réel d'un job (WebSocket) |
| POST    | `/deanonymize`               | Désanonymise un texte en utilisant un mapping    |
| GET     | `/health`                    | Vérifie le bon fonctionnement de l’API           |

📘 Documentation interactive disponible sur : [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔄 API Asynchrone – Détail

### `POST /anonymize/`

Lance un job d’anonymisation en arrière-plan.

**Paramètres :**

- `file` : fichier à anonymiser (`multipart/form-data`)
- `config_options` : chaîne JSON des options d’anonymisation (ex. : entités à exclure, règles personnalisées)
- `file_type` *(optionnel)*
- `has_header` *(optionnel)*

**Exemple de réponse :**
```json
{
  "job_id": "uuid-unique-du-job",
  "status": "pending"
}
```

### `GET /anonymize_status/{job_id}`

Retourne le statut du job :

- `pending` : en cours
- `finished` : terminé
- `error` : échec

**Exemple de réponse (job terminé) :**
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
### `WS /ws/{job_id}`

Ouvre une connexion WebSocket pour suivre en temps réel le statut d'un job. La connexion se ferme lorsque le statut devient `finished` ou `error`.


---

## 🏗️ Structure du dossier

```
anonyfiles_api/
├── api.py                 # Point d’entrée FastAPI (app, middlewares)
├── core_config.py         # Configuration globale (logger, chemins, etc.)
├── job_utils.py           # Gestion et suivi des jobs
└── routers/               # Routers FastAPI
    ├── anonymization.py     # Endpoints /anonymize et /anonymize_status
    ├── deanonymization.py   # Endpoint /deanonymize
    ├── files.py             # Téléchargement des fichiers anonymisés
    └── jobs.py              # Suppression et gestion avancée des jobs
```

Extrait montrant l’utilisation du moteur partagé :

```python
from anonyfiles_core import AnonyfilesEngine

@router.post("/anonymize")
async def anonymize(file: UploadFile):
    engine = AnonyfilesEngine(config_path)
    return await engine.anonymize_async(file)
```

---

## 💡 Conseils

- Toujours lancer depuis la racine du projet pour éviter les erreurs d’import.
- Pour un déploiement en production : utiliser Gunicorn ou Uvicorn avec Nginx, ou un service cloud (Render, Railway, etc.).

---

## 📚 Ressources utiles

- [FastAPI](https://fastapi.tiangolo.com/)
- [Uvicorn](https://www.uvicorn.org/)
- [Projet Anonyfiles sur GitHub](https://github.com/simongrossi/anonyfiles)

---

## 👤 Auteur principal

**Simon Grossi**  
Créateur du projet Anonyfiles – pour une anonymisation rapide, robuste, réversible.
