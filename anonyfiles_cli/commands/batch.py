# anonyfiles_cli/commands/batch.py

import typer
from pathlib import Path
from typing import Optional, List

from ..handlers.batch_handler import BatchHandler
from ..handlers.validation_handler import ValidationHandler # Pour la validation, si nécessaire
from ..ui.console_display import ConsoleDisplay
from ..exceptions import AnonyfilesError # Assurez-vous d'importer les exceptions nécessaires

app = typer.Typer(help="Commandes pour le traitement de fichiers en lot.")
console = ConsoleDisplay()

# Définition des codes de sortie pour Typer
class ExitCodes:
    SUCCESS = 0
    USER_CANCEL = 1
    GENERAL_ERROR = 2
    CONFIG_ERROR = 3
    PROCESSING_ERROR = 4


@app.command(name="process", help="Traite plusieurs fichiers dans un répertoire en lot.")
def process_batch(
    input_dir: Path = typer.Argument(..., help="Dossier contenant les fichiers à traiter.", exists=True, file_okay=False, dir_okay=True, readable=True),
    pattern: str = typer.Option("*", "--pattern", help="Pattern de fichiers à inclure (ex: *.txt, *.csv)."),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Dossier où écrire les fichiers de sortie. Par défaut, un sous-dossier 'anonymized_output' dans le dossier d'entrée."),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Fichier de configuration YAML commun à appliquer à tous les fichiers du lot (optionnel).", exists=True, file_okay=True, dir_okay=False, readable=True),
    dry_run: bool = typer.Option(False, "--dry-run", help="Mode simulation : affiche les actions sans modifier les fichiers."),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recherche les fichiers de manière récursive dans les sous-dossiers."),
    csv_no_header: bool = typer.Option(False, "--csv-no-header", help="Indique que les fichiers CSV d'entrée N'ONT PAS d'en-tête (s'applique à tous les CSV du lot)."),
    has_header_opt: Optional[str] = typer.Option(None, "--has-header-opt", help="Spécifie explicitement si les fichiers CSV d'entrée ont une en-tête ('true'/'false'). Prioritaire sur --csv-no-header pour le lot.")
):
    """
    Lance le traitement d'anonymisation sur un ensemble de fichiers.
    """
    try:
        # Aucune validation spécifique des inputs du batch ici, car le handler le fera
        # ou les options spécifiques aux fichiers individuels sont passées au handler.
        
        handler = BatchHandler(console)
        handler.process_directory(
            input_dir=input_dir,
            pattern=pattern,
            output_dir=output_dir,
            config=config,
            dry_run=dry_run,
            recursive=recursive,
            csv_no_header=csv_no_header,
            has_header_opt=has_header_opt
        )
        # La méthode process_directory lève une exception si l'utilisateur annule ou si input_dir est invalide.
        # Sinon, elle retourne True pour succès ou None.
        
        # Le handler gère déjà la sortie console et les erreurs.
        # Ici, on lève une exception Typer.Exit si une erreur non gérée par le handler survient.

    except AnonyfilesError as e:
        console.handle_error(e, "batch_command_setup")
        raise typer.Exit(code=e.exit_code) # Utilise l'exit_code défini dans AnonyfilesError

    except Exception as e:
        console.handle_error(e, "batch_command_unexpected")
        raise typer.Exit(code=ExitCodes.GENERAL_ERROR)
