
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
- Traitement **asynchrone** avec file de jobs interne, suivi par `job_id`,
  retry, timeout, annulation et progression par phase
- Runtime FastAPI géré par `lifespan` : démarrage/arrêt ordonné de la file de
  jobs et de la purge périodique
- Nettoyage automatique des fichiers temporaires
- CORS activé pour utilisation avec le frontend GUI
- Limitation de débit intégrée pour prévenir les abus (slowapi)
- Auth API optionnelle par clé, activable via `ANONYFILES_API_KEY`

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
| GET     | `/deanonymize_status/{job_id}` | Vérifie le statut d’un job de désanonymisation |
| GET     | `/jobs/queue`                | Compteurs de la file de jobs interne             |
| POST    | `/jobs/{job_id}/cancel`      | Demande l’annulation d’un job                    |
| GET     | `/health`                    | Vérifie le fonctionnement de l’API + diagnostic spaCy |
| GET     | `/health/spacy`              | Diagnostic détaillé du modèle spaCy configuré    |

📘 Documentation interactive disponible sur : [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔐 Authentification optionnelle

Par défaut, l'API reste ouverte pour préserver le développement local et le
sidecar desktop. Pour un déploiement exposé, définissez `ANONYFILES_API_KEY`.
Les endpoints de traitement exigent alors l'un des headers suivants :

```http
X-API-Key: votre-cle
Authorization: Bearer votre-cle
```

Restent publics : `/`, `/health`, `/health/spacy`, `/docs`, `/openapi.json`.
Le WebSocket `/ws/{job_id}` accepte aussi `X-API-Key`, `Authorization: Bearer`,
ou les query params `api_key` / `token` pour les clients qui ne peuvent pas
poser de headers WebSocket.

Exemple :

```bash
ANONYFILES_API_KEY="$(openssl rand -hex 32)" uvicorn anonyfiles_api.api:app --host 0.0.0.0 --port 8000
curl -H "X-API-Key: $ANONYFILES_API_KEY" http://localhost:8000/jobs/queue
```

La GUI peut transmettre une clé via `VITE_ANONYFILES_API_KEY` pour les
déploiements privés. Ne considérez pas cette variable comme secrète dans un
frontend web public : elle est incluse dans le bundle navigateur.

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
  "status": "pending",
  "state": "queued"
}
```

### `GET /anonymize_status/{job_id}`

Retourne le statut du job :

- `pending` : en attente ou en cours
- `finished` : terminé
- `error` : échec
- `cancelled` : annulé
- `timeout` : interrompu par timeout

Le payload contient aussi les métadonnées d'exploitation quand elles sont
disponibles :

- `state`, `progress`, `attempt`, `max_attempts` et timestamps ;
- `file_size_bytes`, `file_type`, `job_kind`, `timeout_seconds` ;
- `duration_seconds`, `queue_wait_seconds`, `phase_durations_seconds` ;
- `entities_detected_count`, `total_replacements` ;
- `final_status_category` (`success`, `engine_error`, `unexpected_error`,
  `timeout`, `cancelled`, etc.).

`state` décrit la phase courante (`queued`, `running`, `preparing`,
`processing`, `finalizing`, `retrying`, `cancelling`, etc.). Les logs API
publient aussi des événements structurés préfixés par `job_event`.

**Exemple de réponse (job terminé) :**
```json
{
  "status": "finished",
  "state": "completed",
  "progress": 100,
  "final_status_category": "success",
  "duration_seconds": 2.184,
  "phase_durations_seconds": {
    "queued": 0.012,
    "running": 0.006,
    "preparing": 0.041,
    "processing": 2.001,
    "finalizing": 0.124
  },
  "file_size_bytes": 15342,
  "file_type": "txt",
  "entities_detected_count": 12,
  "total_replacements": 12,
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

Ouvre une connexion WebSocket pour suivre en temps réel le statut d'un job. La connexion se ferme lorsque le statut devient `finished`, `error`, `cancelled` ou `timeout`.

### `GET /jobs/queue`

Retourne les compteurs de la file en mémoire :

```json
{
  "queued": 0,
  "running": 1,
  "workers": 1
}
```

### `GET /health`

Retourne l'état de l'API et le diagnostic spaCy sans charger le modèle complet :

```json
{
  "status": "ok",
  "spacy": {
    "status": "ok",
    "ready": true,
    "python_version": "3.11.15",
    "spacy": {"installed": true, "version": "3.8.14"},
    "model": {
      "name": "fr_core_news_md",
      "installed": true,
      "version": "3.8.0",
      "spacy_version_constraint": ">=3.8.0,<3.9.0",
      "compatible": true
    },
    "commands": {
      "install_model": "python -m spacy download fr_core_news_md",
      "repair_model": "python -m spacy download fr_core_news_md",
      "validate_models": "python -m spacy validate"
    }
  }
}
```

`GET /health/spacy` retourne directement le bloc `spacy`.

### `POST /jobs/{job_id}/cancel`

Demande l'annulation d'un job. L'annulation est immédiate pour un job encore en
file. Pour un job déjà en cours, l'API publie `state: "cancelling"` puis protège
le statut final `cancelled` lorsque le worker reprend la main.

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
HEADERS = {"X-API-Key": "votre-cle"}  # optionnel, seulement si ANONYFILES_API_KEY est défini

# 1. ENVOI DU FICHIER
# On envoie le fichier et on récupère immédiatement un Job ID
with open("contrat.pdf", "rb") as f:
    response = requests.post(
        f"{API_URL}/anonymize",
        headers=HEADERS,
        files={"file": f},
        data={"config_options": "{}"},
    )
job_data = response.json()
job_id = job_data["job_id"]
print(f"✅ Job créé : {job_id} (Statut: {job_data['status']})")

# 2. ATTENTE DU RÉSULTAT (Polling)
# On vérifie le statut toutes les secondes
while True:
    status_res = requests.get(f"{API_URL}/anonymize_status/{job_id}", headers=HEADERS)
    status_data = status_res.json()
    state = status_data["status"]
    
    if state == "finished":
        print("🎉 Traitement terminé !")
        break
    elif state in {"error", "cancelled", "timeout"}:
        print(f"❌ Erreur : {status_data.get('error')}")
        exit(1)
    
    print(f"⏳ {status_data.get('state')} - {status_data.get('progress', 0)}%")
    time.sleep(1)

# 3. RÉCUPÉRATION DES FICHIERS
# Une fois fini, on télécharge le résultat
# L'URL de téléchargement suit souvent le format : /files/{job_id}/{filename}
# Ou est fournie dans la réponse 'finished' (selon implémentation)
download_url = f"{API_URL}/files/{job_id}/anonymized_contrat.pdf"
content = requests.get(download_url, headers=HEADERS).content

with open("contrat_anonymise.pdf", "wb") as f:
    f.write(content)
print("📂 Fichier anonymisé sauvegardé.")
```

### 🐚 Scénario typique (cURL)

**Étape 1 : Envoyer le fichier**
```bash
curl -X POST "http://localhost:8000/anonymize" \
     -H "X-API-Key: votre-cle" \
     -F "file=@mon_document.txt" \
     -F 'config_options={}'
# Réponse : {"job_id": "1234-5678", "status": "pending", "state": "queued"}
```

**Étape 2 : Vérifier le statut**
```bash
curl -H "X-API-Key: votre-cle" "http://localhost:8000/anonymize_status/1234-5678"
# Réponse tant que ça tourne : {"status": "pending", "state": "processing", "progress": 45}
# Réponse quand fini : {"status": "finished", "files": ["mon_document_anonymized.txt"]}
```

**Annuler un job**
```bash
curl -X POST "http://localhost:8000/jobs/1234-5678/cancel" \
     -H "X-API-Key: votre-cle"
# Réponse : {"status": "cancelled", "state": "cancelled", "cancel_requested": true}
```

**Étape 3 : Télécharger**
```bash
curl -H "X-API-Key: votre-cle" -O "http://localhost:8000/files/1234-5678/mon_document_anonymized.txt"
```

## 🏗️ Structure du dossier

```
anonyfiles_api/
├── api.py                 # Point d’entrée FastAPI (app, middlewares)
├── auth.py                # Auth API optionnelle par clé
├── core_config.py         # Configuration globale (logger, chemins, etc.)
├── job_queue.py           # File de jobs interne (workers, retry, timeout)
├── job_utils.py           # Gestion et suivi des statuts de jobs
└── routers/               # Routers FastAPI
    ├── anonymization.py     # Endpoints /anonymize et /anonymize_status
    ├── deanonymization.py   # Endpoint /deanonymize
    ├── files.py             # Téléchargement des fichiers anonymisés
    └── jobs.py              # Suppression et gestion avancée des jobs
```

Extrait simplifié de l'orchestration côté API :

```python
from anonyfiles_api.job_queue import ensure_job_queue

@router.post("/anonymize")
async def anonymize(request: Request, file: UploadFile):
    job_queue = await ensure_job_queue(request.app)
    await job_queue.enqueue(
        job_id=job_id,
        kind="anonymization",
        func=run_anonymization_job_sync,
        kwargs={...},
    )
    return {"job_id": job_id, "status": "pending", "state": "queued"}
```
La file exécute ensuite le moteur dans un worker thread, avec statut persistant
dans `status.json`.

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
