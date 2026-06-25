# API REST Reference

L'API **Anonyfiles** permet d'intégrrer les fonctionnalités d'anonymisation et de désanonymisation dans vos propres applications, workflows ou services tiers. Elle est construite avec **FastAPI** et conçue pour être performante et asynchrone.

Le endpoint `POST /anonymize_preview/` permet de prévisualiser les entités
détectées en dry-run avant de lancer le job final. Le job `POST /anonymize/`
accepte ensuite `entity_decisions` pour exclure ou corriger des entités précises.

---

## 🚀 Démarrage

### Lancement Local (Développement)

```bash
uvicorn anonyfiles_api.api:app --reload --host 0.0.0.0 --port 8000
```

Une fois lancé :

- Documentation interactive (Swagger UI) : <http://localhost:8000/docs>
- Spécification OpenAPI (JSON) : <http://localhost:8000/openapi.json>

---

## 🔄 Workflow Asynchrone (Jobs)

Pour gérer efficacement les fichiers volumineux et les temps de traitement NLP, l'API fonctionne de manière asynchrone.

Étapes :

1. **Soumission (POST)** — envoi du fichier, retour immédiat `job_id` + `pending/queued`
2. **Traitement** — file de jobs interne avec workers, retry, timeout et annulation
3. **Suivi (GET / WS)** — récupération du statut enrichi (`state`, `progress`, métriques)
4. **Récupération** — téléchargement des fichiers résultants

---

## 🔗 Endpoints Principaux

### 1. Anonymisation

#### **POST** `/anonymize`

Crée un nouveau job d'anonymisation.

**Body (multipart/form-data)** :

| Champ | Requis | Type | Description |
|---|---|---|---|
| `file` | ✔ | fichier | Document à traiter |
| `config_options` | ✔ | JSON | Options d'anonymisation (`{}` pour les valeurs par défaut) |
| `has_header` | ✖ | bool | Pour CSV |

**Réponse (200 OK)** :

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "state": "queued"
}
```

#### **GET** `/anonymize_status/{job_id}`

Récupère l'état d'un job.

**Réponse (pending)** :

```json
{
  "status": "pending",
  "state": "processing",
  "progress": 45,
  "attempt": 1,
  "max_attempts": 1,
  "file_size_bytes": 15342,
  "file_type": "txt"
}
```

**Réponse (finished)** :

```json
{
  "status": "finished",
  "state": "completed",
  "progress": 100,
  "final_status_category": "success",
  "duration_seconds": 2.184,
  "queue_wait_seconds": 0.012,
  "phase_durations_seconds": {
    "queued": 0.012,
    "processing": 2.001,
    "finalizing": 0.124
  },
  "entities_detected_count": 12,
  "total_replacements": 12,
  "audit_log": []
}
```

#### **WS** `/ws/{job_id}`

WebSocket permettant de suivre l'évolution en temps réel.

La connexion se ferme sur `finished`, `error`, `cancelled` ou `timeout`.

---

### 2. Désanonymisation

#### **POST** `/deanonymize`

Restaure un fichier anonymisé via un mapping.

**Body (multipart/form-data)** :

| Champ | Requis | Description |
|---|---|---|
| `file` | ✔ | Fichier anonymisé |
| `mapping` | ✔ | Mapping CSV |

---

### 3. Utilitaires

#### **GET** `/health`

Permet de vérifier l'état du service et le diagnostic spaCy.

**Réponse** :

```json
{
  "status": "ok",
  "spacy": {
    "status": "ok",
    "ready": true,
    "model": {
      "name": "fr_core_news_md",
      "installed": true,
      "version": "3.8.0",
      "compatible": true
    },
    "commands": {
      "install_model": "python -m spacy download fr_core_news_md",
      "validate_models": "python -m spacy validate"
    }
  }
}
```

#### **GET** `/health/spacy`

Retourne directement le diagnostic spaCy détaillé.

#### **GET** `/jobs/queue`

Retourne les compteurs de la file interne.

```json
{"queued": 0, "running": 1, "workers": 1}
```

#### **POST** `/jobs/{job_id}/cancel`

Demande l'annulation d'un job en attente ou en cours.

```json
{"status": "cancelled", "state": "cancelled", "cancel_requested": true}
```

---

## 💻 Exemples d'utilisation

### Avec `curl`

**1. Envoyer un fichier**

```bash
curl -X POST "http://localhost:8000/anonymize"   -F "file=@contrat.pdf"
```

**2. Vérifier le statut**

```bash
curl "http://localhost:8000/anonymize_status/abc-123"
```

**3. Télécharger le résultat**

```bash
curl -O "http://localhost:8000/files/abc-123/contrat_anonymized.pdf"
```

---

### Avec Python (`requests`)

```python
import requests
import time

API = "http://localhost:8000"

with open("data.xlsx", "rb") as f:
    res = requests.post(
        f"{API}/anonymize",
        files={"file": f},
        data={"config_options": "{}"},
    )
    job_id = res.json()["job_id"]

while True:
    status = requests.get(f"{API}/anonymize_status/{job_id}").json()
    if status["status"] in ["finished", "error", "cancelled", "timeout"]:
        break
    time.sleep(1)

if status["status"] == "finished":
    print("Fichiers disponibles :", status["files"])
```

---

## 📦 Déploiement

Pour la mise en production, consulter `deploy/`.

- Docker (build multi-stage optimisé)
- Systemd (`deploy/anonyfiles-api.service`)

### Variables d'environnement

| Variable | Description |
|---|---|
| `ANONYFILES_JOBS_DIR` | Dossier de stockage |
| `ANONYFILES_MAX_UPLOAD_SIZE_MB` | Taille max d'un upload (Mio, défaut 100) |
| `ANONYFILES_JOB_RETENTION_HOURS` | TTL des jobs avant purge auto (h, défaut 24, 0=off) |
| `ANONYFILES_JOB_PURGE_INTERVAL_MINUTES` | Intervalle de purge (min, défaut 60) |
| `ANONYFILES_CORS_ORIGINS` | Origines autorisées CORS |
| `ANONYFILES_API_KEY` | Clé API optionnelle. Si définie, envoyer `X-API-Key` ou `Authorization: Bearer`. |
