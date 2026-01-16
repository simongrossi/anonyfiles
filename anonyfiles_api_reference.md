# API REST Reference

L'API **Anonyfiles** permet d'intégrrer les fonctionnalités d'anonymisation et de désanonymisation dans vos propres applications, workflows ou services tiers. Elle est construite avec **FastAPI** et conçue pour être performante et asynchrone.

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

1. **Soumission (POST)** — envoi du fichier, retour immédiat `job_id` + `pending`
2. **Traitement** — exécution en arrière-plan
3. **Suivi (GET / WS)** — récupération du statut
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
| `config_options` | ✖ | JSON | Surcharge de config |
| `has_header` | ✖ | bool | Pour CSV |

**Réponse (200 OK)** :

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending"
}
```

#### **GET** `/anonymize_status/{job_id}`

Récupère l'état d'un job.

**Réponse (pending)** :

```json
{"status": "pending"}
```

**Réponse (finished)** :

```json
{
  "status": "finished",
  "files": [
    "http://localhost:8000/files/job_id/fichier_anonymise.txt",
    "http://localhost:8000/files/job_id/mapping.csv"
  ],
  "audit_log": []
}
```

#### **WS** `/ws/{job_id}`

WebSocket permettant de suivre l'évolution en temps réel.

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

Permet de vérifier l'état du service.

**Réponse** :

```json
{"status": "ok", "version": "..."}
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
    res = requests.post(f"{API}/anonymize", files={"file": f})
    job_id = res.json()["job_id"]

while True:
    status = requests.get(f"{API}/anonymize_status/{job_id}").json()
    if status["status"] in ["finished", "error"]:
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
| `ANONYFILES_CORS_ORIGINS` | Origines autorisées CORS |

