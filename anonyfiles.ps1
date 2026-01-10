Write-Host "Anonyfiles - Script PowerShell"
Write-Host "----------------------------------"
Write-Host "Commandes disponibles :"
Write-Host "  setup  : Création des environnements virtuels"
Write-Host "  api    : Lancer l'API FastAPI"
Write-Host "  cli    : Lancer le moteur CLI"
Write-Host "  gui    : Lancer l'interface graphique"
Write-Host "  clean  : Supprimer les environnements virtuels"
Write-Host ""

param (
    [ValidateSet("setup", "api", "cli", "gui", "clean")]
    [string]$action
)

switch ($action) {
    "setup" {
        Write-Host "🔧 Setup des environnements..."
        .\setup_envs.ps1
    }
    "api" {
        Write-Host "🚀 Lancement de l'API..."
        & ".\env-api\Scripts\uvicorn.exe" anonyfiles_api.api:app --host 127.0.0.1 --port 8000 --reload
    }
    "cli" {
        Write-Host "▶️ Lancement du CLI..."
        # Transfère les arguments supplémentaires ($args) à la commande anonyfiles-cli
        & ".\env-cli\Scripts\anonyfiles-cli.exe" $args
    }
    "gui" {
        Write-Host "🖥️ Lancement de la GUI (Tauri)..."
        cd anonyfiles_gui
        npm run tauri dev
    }
    "clean" {
        Write-Host "🧹 Suppression des environnements..."
        Remove-Item -Recurse -Force env-cli, env-api, env-gui
    }
    Default {
        Write-Host "❌ Action non reconnue. Utilisez: setup, api, cli, gui ou clean."
    }
}
