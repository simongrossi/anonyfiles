Write-Host "➡️  Création des environnements..."

python -m venv env-cli
python -m venv env-api
python -m venv env-gui

Write-Host "📦 Installation des dépendances..."

.\env-cli\Scripts\Activate.ps1
pip install -e .[dev]
deactivate

.\env-api\Scripts\Activate.ps1
pip install -e .
deactivate

if (Test-Path GUI\requirements.txt) {
    .\env-gui\Scripts\Activate.ps1
    pip install -r GUI\requirements.txt
    deactivate
} else {
    Write-Host "✅ Aucun requirements.txt dans GUI"
}

Write-Host "✅ Tous les environnements sont prêts."
