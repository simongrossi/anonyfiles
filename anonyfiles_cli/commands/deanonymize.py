# anonyfiles_cli/commands/deanonymize.py

import typer
from pathlib import Path
from typing import Optional, List

from ..handlers.deanonymize_handler import DeanonymizeHandler
from ..handlers.validation_handler import ValidationHandler
from ..ui.console_display import ConsoleDisplay
from ..exceptions import AnonyfilesError # Assurez-vous d'importer les exceptions nécessaires

app = typer.Typer(help="Commandes pour désanonymiser les fichiers.")
console = ConsoleDisplay()

# Définition des codes de sortie pour Typer
class ExitCodes:
    SUCCESS = 0
    USER_CANCEL = 1
    GENERAL_ERROR = 2
    CONFIG_ERROR = 3
    PROCESSING_ERROR = 4


@app.command(name="process", help="Désanonymise un fichier en utilisant un mapping CSV.")
def process_deanonymize(
    input_file: Path = typer.Argument(..., help="Fichier à désanonymiser", exists=True, file_okay=True, dir_okay=False, readable=True),
    mapping_csv: Path = typer.Option(..., help="Mapping CSV à utiliser", exists=True, file_okay=True, dir_okay=False, readable=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Fichier de sortie restauré (optionnel)."),
    report: Optional[Path] = typer.Option(None, "--report", help="Fichier de rapport détaillé JSON sur la désanonymisation (optionnel)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulation sans écriture de fichiers."),
    permissive: bool = typer.Option(False, "--permissive", help="Tolère les codes inconnus dans le mapping et restaure ce qui peut l'être (mode non-strict).")
):
    """
    Désanonymise un fichier anonymisé à partir d'un mapping CSV fourni.
    """
    try:
        # 1. Validation des entrées de la commande
        ValidationHandler.validate_deanonymize_inputs(
            input_file=input_file,
            mapping_csv=mapping_csv
        )

        # 2. Instanciation et appel du handler métier
        handler = DeanonymizeHandler(console)
        success = handler.process(
            input_file=input_file,
            mapping_csv=mapping_csv,
            output=output,
            report=report,
            dry_run=dry_run,
            permissive=permissive
        )

        if not success:
            # Le handler gère déjà l'affichage des erreurs, on sort juste avec un code d'échec
            raise typer.Exit(code=ExitCodes.GENERAL_ERROR)

    except AnonyfilesError as e:
        console.handle_error(e, "deanonymize_command_validation_or_setup")
        raise typer.Exit(code=ExitCodes.CONFIG_ERROR)

    except Exception as e:
        console.handle_error(e, "deanonymize_command_unexpected")
        raise typer.Exit(code=ExitCodes.GENERAL_ERROR)