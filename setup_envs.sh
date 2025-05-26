#!/bin/bash
set -e

echo "➡️  Création des environnements..."

python3 -m venv anonyfiles-cli/venv
python3 -m venv anonyfiles_api/venv
python3 -m venv anonyfiles-gui/venv

echo "📦 Installation des dépendances..."

echo "🔧 CLI"
source anonyfiles-cli/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r anonyfiles-cli/requirements.txt
deactivate

echo "🔧 API"
source anonyfiles_api/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r anonyfiles_api/requirements.txt
deactivate

if [ -f anonyfiles-gui/requirements.txt ]; then
  echo "🔧 GUI"
  source anonyfiles-gui/venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -r anonyfiles-gui/requirements.txt
  deactivate
else
  echo "✅ Aucun requirements.txt dans anonyfiles-gui"
fi

echo "✅ Tous les environnements sont prêts."
