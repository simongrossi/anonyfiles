# anonyfiles_cli/main.py
# -*- coding: utf-8 -*-
#
# Entrée du programme CLI
import typer
import logging

# Importe les applications Typer des modules de commandes séparés
from anonyfiles_cli.commands import anonymize, deanonymize, config, batch, utils, clean_job, logs
from anonyfiles_cli.managers.config_manager import ConfigManager
from anonyfiles_cli.ui.console_display import ConsoleDisplay
from anonyfiles_cli.cli_logger import CLIUsageLogger

app = typer.Typer(pretty_exceptions_show_locals=False, help="Anonyfiles CLI - Outil d'anonymisation de documents.", rich_markup_mode="rich")
console = ConsoleDisplay()

# Ajout des sous-commandes depuis les modules séparés
app.add_typer(anonymize.app, name="anonymize", help="Commandes pour anonymiser les fichiers.")
app.add_typer(deanonymize.app, name="deanonymize", help="Commandes pour desanonymiser les fichiers.")
app.add_typer(config.app, name="config", help="Gère la configuration d'Anonyfiles.")
app.add_typer(batch.app, name="batch", help="Traite des fichiers en lot.")
app.add_typer(utils.app, name="utils", help="Commandes utilitaires diverses.")
app.add_typer(logs.app, name="logs", help="Anonymise des fichiers de log en utilisant des profils spécialisés.")
app.add_typer(clean_job.app, name="job", help="Gère et nettoie les répertoires de jobs (suppression, listage).") # <--- AJOUTEZ CETTE LIGNE


@app.callback()
def main_callback(
    ctx: typer.Context,
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Affiche les messages de debug"
    ),
):
    """
    Fonction de rappel principale.
    S'assure qu'un fichier de configuration utilisateur par défaut existe au démarrage de l'application
    s'il n'est pas déjà présent.
    """
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO, force=True)
    if verbose:
        logging.debug("Verbose mode enabled")
    CLIUsageLogger.VERBOSE = verbose

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
