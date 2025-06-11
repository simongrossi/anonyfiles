# anonyfiles_cli/commands/anonymize.py

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any

from ..handlers.anonymize_handler import AnonymizeHandler
from ..handlers.validation_handler import ValidationHandler
from ..ui.console_display import ConsoleDisplay
from ..ui.interactive_mode import prompt_entities_to_exclude
from ..exceptions import AnonyfilesError # Assurez-vous d'importer les exceptions nécessaires

app = typer.Typer(help="Commandes pour anonymiser les fichiers.")
console = ConsoleDisplay()

# Définition des codes de sortie pour Typer
class ExitCodes:
    SUCCESS = 0
    USER_CANCEL = 1
    GENERAL_ERROR = 2
    CONFIG_ERROR = 3
    PROCESSING_ERROR = 4


@app.command(name="process", help="Anonymise un fichier en fonction des options fournies.")
def process_anonymize(
    input_file: Path = typer.Argument(..., help="Fichier à anonymiser", exists=True, file_okay=True, dir_okay=False, readable=True),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Fichier de configuration YAML (optionnel). S'il est fourni, il doit exister.", exists=True, file_okay=True, dir_okay=False, readable=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Chemin du fichier de sortie anonymisé (optionnel)."),
    log_entities: Optional[Path] = typer.Option(None, "--log-entities", help="Chemin du fichier CSV de log des entités détectées (optionnel)."),
    mapping_output: Optional[Path] = typer.Option(None, "--mapping-output", help="Chemin du fichier CSV du mapping d'anonymisation (optionnel)."),
    bundle: Optional[Path] = typer.Option(None, "--bundle", "--output-bundle", help="Chemin du fichier zip regroupant toutes les sorties (optionnel)."),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="Dossier où écrire les fichiers de sortie par défaut (si les chemins spécifiques ne sont pas fournis).", file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulation sans écriture de fichiers."),
    csv_no_header: bool = typer.Option(False, "--csv-no-header", help="Indique que le fichier CSV d'entrée N'A PAS d'en-tête (utilisé si --has-header-opt n'est pas fourni)."),
    has_header_opt: Optional[str] = typer.Option(None, "--has-header-opt", help="Spécifie explicitement si le fichier CSV d'entrée a une en-tête ('true'/'false'). Prioritaire sur --csv-no-header."),
    exclude_entities: Optional[List[str]] = typer.Option(None, "--exclude-entities", help="Types d'entités à exclure, séparés par des virgules (ex: PER,LOC)."),
    interactive: bool = typer.Option(False, "--interactive", "-i", help="Sélection interactive des entités à anonymiser."),
    custom_replacements_json: Optional[str] = typer.Option(None, "--custom-replacements-json", help="Chaîne JSON des règles de remplacement personnalisées (ex: '[{\"pattern\": \"Confidentiel\", \"replacement\": \"[SECRET]\"}]')."),
    append_timestamp: bool = typer.Option(True, help="Ajoute un timestamp aux noms des fichiers de sortie par défaut."),
    force: bool = typer.Option(False, "--force", "-f", help="Force l’écrasement des fichiers de sortie existants.")
):
    """
    Anonymise un fichier en appliquant la détection d'entités et les règles de remplacement.
    """
    try:
        # 1. Validation des entrées de la commande
        ValidationHandler.validate_anonymize_inputs(
            input_file=input_file,
            output=output,
            custom_replacements_json=custom_replacements_json,
            csv_no_header=csv_no_header,
            has_header_opt=has_header_opt
        )
        
        # 2. Sélection interactive des entités le cas échéant
        if interactive and not exclude_entities:
            exclude_entities = prompt_entities_to_exclude(console)
        elif interactive and exclude_entities:
            console.console.print("[yellow]--interactive ignoré car --exclude-entities est déjà fourni.[/yellow]")

        # 3. Instanciation et appel du handler métier
        handler = AnonymizeHandler(console)
        success = handler.process(
            input_file=input_file,
            config_path=config,
            output=output,
            log_entities=log_entities,
            mapping_output=mapping_output,
            bundle_output=bundle,
            output_dir=output_dir,
            dry_run=dry_run,
            csv_no_header=csv_no_header,
            has_header_opt=has_header_opt,
            exclude_entities=exclude_entities,
            custom_replacements_json=custom_replacements_json,
            append_timestamp=append_timestamp,
            force=force
        )

        if not success:
            raise typer.Exit(code=ExitCodes.GENERAL_ERROR) # Le handler gère déjà l'affichage des erreurs

    except AnonyfilesError as e:
        console.handle_error(e, "anonymize_command_validation_or_setup")
        raise typer.Exit(code=ExitCodes.CONFIG_ERROR) # ou l'exit code approprié à l'erreur

    except typer.Exit:
        raise

    except Exception as e:
        console.handle_error(e, "anonymize_command_unexpected")
        raise typer.Exit(code=ExitCodes.GENERAL_ERROR)
