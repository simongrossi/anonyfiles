#!/bin/bash
set -e

echo "🚀 Lancement de l’API FastAPI..."

cd "$(dirname "$0")/anonyfiles_api"
source venv/bin/activate

echo "📂 Répertoire courant : $(pwd)"
echo "PYTHONPATH=.. uvicorn anonyfiles_api.api:app --host 127.0.0.1 --port 8000"

PYTHONPATH=.. uvicorn anonyfiles_api.api:app --host 127.0.0.1 --port 8000
