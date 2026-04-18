
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
- Limitation de débit intégrée pour prévenir les abus (slowapi)

---

## 🛠️ Prérequis

- Python 3.11+
- [pip](https://pip.pypa.io/)
- Modèle spaCy `fr_core_news_md`

---

## ⚡ Installation

Le projet utilise `pyproject.toml` comme source unique de dépendances. Depuis la racine du repo :

```bash
pip install -e .
python -m spacy download fr_core_news_md
```

Extras disponibles :

- `pip install -e ".[dev]"` — pytest, ruff, black, bandit, safety, pip-audit
- `pip install -e ".[packaging]"` — PyInstaller (pour builder l'API comme sidecar desktop)

---

## 🏃‍♂️ Lancement du serveur de développement

```bash
uvicorn anonyfiles_api.api:app --reload --host 0.0.0.0 --port 8000
```

Ou via le module standalone (même entry point que le sidecar desktop) :

```bash
python -m anonyfiles_api --host 127.0.0.1 --port 8000
```

## 📦 Modes de déploiement

Cette API est lancée de 3 manières selon le contexte, mais **le code est identique** :

| Mode | Lancement | Docs |
|---|---|---|
| Serveur (Docker, Railway, systemd) | `uvicorn anonyfiles_api.api:app` | [`../deploy/README.md`](../deploy/README.md) |
| Web (via docker-compose) | nginx → uvicorn dans le même compose | [`../guide_installation_anonyfiles.md`](../guide_installation_anonyfiles.md) |
| Desktop autonome | binaire PyInstaller spawné par Tauri | [`../anonyfiles_architecture.md`](../anonyfiles_architecture.md) |

Le entry point PyInstaller est [`anonyfiles_api/__main__.py`](__main__.py), qui parse `--host`/`--port` et lance `uvicorn.run(app, ...)`.

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

## 🚦 Workflow complet : Pas à pas

L'API Anonyfiles est **asynchrone** (basée sur des jobs). Cela signifie que le traitement ne bloque pas votre requête : vous déposez un fichier, recevez un ticket (Job ID), et revenez chercher le résultat plus tard.

### 📊 Pourquoi asynchrone ?

| Avantage | Explication |
| :--- | :--- |
| **Gros fichiers** | Permet d'uploader et traiter des fichiers de plusieurs Go sans timeout HTTP. |
| **Non-bloquant** | Votre application cliente n'est pas "gelée" pendant l'analyse NLP (qui peut être longue). |
| **Robustesse** | Si le client perd la connexion, le traitement serveur continue. |

### 👣 Scénario typique (Python)

Voici comment orchestrer une anonymisation complète en Python avec `requests`.

```python
import requests
import time

API_URL = "http://localhost:8000"

# 1. ENVOI DU FICHIER
# On envoie le fichier et on récupère immédiatement un Job ID
with open("contrat.pdf", "rb") as f:
    response = requests.post(f"{API_URL}/anonymize", files={"file": f})
job_data = response.json()
job_id = job_data["job_id"]
print(f"✅ Job créé : {job_id} (Statut: {job_data['status']})")

# 2. ATTENTE DU RÉSULTAT (Polling)
# On vérifie le statut toutes les secondes
while True:
    status_res = requests.get(f"{API_URL}/anonymize_status/{job_id}")
    status_data = status_res.json()
    state = status_data["status"]
    
    if state == "finished":
        print("🎉 Traitement terminé !")
        break
    elif state == "error":
        print(f"❌ Erreur : {status_data.get('error')}")
        exit(1)
    
    print("⏳ Traitement en cours...")
    time.sleep(1)

# 3. RÉCUPÉRATION DES FICHIERS
# Une fois fini, on télécharge le résultat
# L'URL de téléchargement suit souvent le format : /files/{job_id}/{filename}
# Ou est fournie dans la réponse 'finished' (selon implémentation)
download_url = f"{API_URL}/files/{job_id}/anonymized_contrat.pdf"
content = requests.get(download_url).content

with open("contrat_anonymise.pdf", "wb") as f:
    f.write(content)
print("📂 Fichier anonymisé sauvegardé.")
```

### 🐚 Scénario typique (cURL)

**Étape 1 : Envoyer le fichier**
```bash
curl -X POST "http://localhost:8000/anonymize" \
     -F "file=@mon_document.txt"
# Réponse : {"job_id": "1234-5678", "status": "pending"}
```

**Étape 2 : Vérifier le statut**
```bash
curl "http://localhost:8000/anonymize_status/1234-5678"
# Réponse tant que ça tourne : {"status": "pending"}
# Réponse quand fini : {"status": "finished", "files": ["mon_document_anonymized.txt"]}
```

**Étape 3 : Télécharger**
```bash
curl -O "http://localhost:8000/files/1234-5678/mon_document_anonymized.txt"
```

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
    # temporary async wrapper around `anonymize`

    return await engine.anonymize_async(file)
```
Cet appel asynchrone utilise simplement ``asyncio.to_thread`` pour exécuter la
méthode de base de façon non bloquante.

---

## 🗒️ Format des logs

Les journaux sont désormais structurés en JSON. Chaque entrée inclut les champs
`endpoint`, `client_ip` et `job_id` permettant de tracer le contexte de la
requête.

Exemple :

```json
{"level": "INFO", "message": "Exemple", "endpoint": "/anonymize", "client_ip": "127.0.0.1", "job_id": "1234"}
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
