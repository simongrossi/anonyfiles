# anonyfiles_cli/main.py

import typer
from pathlib import Path

# Importe les applications Typer des modules de commandes séparés
from .commands import anonymize, deanonymize, config, batch, utils
from .managers.config_manager import ConfigManager
from .ui.console_display import ConsoleDisplay

app = typer.Typer(pretty_exceptions_show_locals=False, help="Anonyfiles CLI - Outil d'anonymisation de documents.")
console = ConsoleDisplay()

# Ajout des sous-commandes depuis les modules séparés
app.add_typer(anonymize.app, name="anonymize", help="Commandes pour anonymiser les fichiers.")
app.add_typer(deanonymize.app, name="deanonymize", help="Commandes pour désanonymiser les fichiers.")
app.add_typer(config.app, name="config", help="Gère la configuration d'Anonyfiles.")
app.add_typer(batch.app, name="batch", help="Traite des fichiers en lot.")
app.add_typer(utils.app, name="utils", help="Commandes utilitaires diverses.")


@app.callback()
def main_callback():
    """
    Fonction de rappel principale.
    S'assure qu'un fichier de configuration utilisateur par défaut existe au démarrage de l'application
    s'il n'est pas déjà présent.
    """
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE
    if not user_config_path.exists():
        console.console.print(f"[dim]ℹ️ Fichier de configuration utilisateur non trouvé. Création d'une configuration par défaut à : {user_config_path}[/dim]")
        try:
            ConfigManager.create_default_user_config()
        except Exception as e:
            console.console.print(f"[bold red]❌ Erreur lors de la création de la configuration par défaut au démarrage : {e}[/bold red]", style="red")
            # Ne pas quitter l'application, mais laisser un avertissement critique.
            # Les commandes suivantes pourront échouer si la config est essentielle.


if __name__ == "__main__":
    app()