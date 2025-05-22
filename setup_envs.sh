#!/bin/bash
set -e

echo "➡️  Création des environnements..."

python3 -m venv env-cli
python3 -m venv env-api
python3 -m venv env-gui

echo "📦 Installation des dépendances..."

source env-cli/bin/activate
pip install -r anonyfiles-cli/requirements.txt
deactivate

source env-api/bin/activate
pip install -r anonyfiles_api/requirements.txt
deactivate

if [ -f anonyfiles-gui/requirements.txt ]; then
  source env-gui/bin/activate
  pip install -r anonyfiles-gui/requirements.txt
  deactivate
else
  echo "✅ Aucun requirements.txt dans anonyfiles-gui"
fi

echo "✅ Tous les environnements sont prêts."
