#!/bin/bash
set -e

echo "➡️  Création des environnements..."

python3 -m venv anonyfiles_cli/venv
python3 -m venv anonyfiles_api/venv
python3 -m venv anonyfiles_gui/venv

echo "📦 Installation des dépendances..."

echo "🔧 CLI"
source anonyfiles_cli/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r anonyfiles_cli/requirements.txt
deactivate

echo "🔧 API"
source anonyfiles_api/venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r anonyfiles_api/requirements.txt
deactivate

if [ -f anonyfiles_gui/requirements.txt ]; then
  echo "🔧 GUI"
  source anonyfiles_gui/venv/bin/activate
  pip install --upgrade pip setuptools wheel
  pip install -r anonyfiles_gui/requirements.txt
  deactivate
else
  echo "✅ Aucun requirements.txt dans anonyfiles_gui"
fi

echo "✅ Tous les environnements sont prêts."
