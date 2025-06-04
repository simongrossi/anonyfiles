# anonyfiles_cli/main.py

import typer
from pathlib import Path
import json
from typing import Optional, List, Dict, Any
import yaml

# Assurez-vous que CLIUsageLogger est bien importable.
from .cli_logger import CLIUsageLogger

# Imports depuis les modules de votre projet
from .anonymizer.anonyfiles_core import AnonyfilesEngine
from .anonymizer.run_logger import log_run_event
from .anonymizer.file_utils import timestamp

# --- NOUVEAUX IMPORTS DES MANAGERS ET EXCEPTIONS ---
from .managers.path_manager import PathManager
from .managers.validation_manager import ValidationManager
from .managers.config_manager import ConfigManager
from .exceptions import AnonyfilesError, ConfigurationError, ProcessingError, FileIOError
from .ui.console_display import ConsoleDisplay

app = typer.Typer(pretty_exceptions_show_locals=False)
console = ConsoleDisplay()


def process_anonymization(
    input_file: Path,
    effective_config: Dict[str, Any],
    paths: Dict[str, Path],
    dry_run: bool,
    exclude_entities_cli: Optional[List[str]],
    custom_replacements_json: Optional[str],
    csv_has_header: Optional[bool]
) -> Dict[str, Any]:
    """
    Encapsule la logique principale d'anonymisation, en utilisant les nouvelles classes.
    """
    try:
        custom_rules_list = ValidationManager.parse_custom_replacements(custom_replacements_json)

        engine = AnonyfilesEngine(
            config=effective_config,
            exclude_entities_cli=exclude_entities_cli,
            custom_replacement_rules=custom_rules_list
        )

        processor_kwargs = {}
        if input_file.suffix.lower() == ".csv" and csv_has_header is not None:
            processor_kwargs['has_header'] = csv_has_header

        result = engine.anonymize(
            input_path=input_file,
            output_path=paths.get("output_file"),
            entities=None,
            dry_run=dry_run,
            log_entities_path=paths.get("log_entities_file"),
            mapping_output_path=paths.get("mapping_file"),
            **processor_kwargs
        )

        if result.get("status") == "error":
            raise ProcessingError(result.get('error', 'Le moteur d\'anonymisation a signalé une erreur.'))
        
        return result
    except AnonyfilesError:
        raise
    except Exception as e:
        raise ProcessingError(f"Erreur inattendue lors du traitement d'anonymisation : {e}") from e


@app.command()
def anonymize(
    input_file: Path = typer.Argument(..., help="Fichier à anonymiser", exists=True, file_okay=True, dir_okay=False, readable=True),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Fichier de configuration YAML (optionnel). S'il est fourni, il doit exister.", exists=True, file_okay=True, dir_okay=False, readable=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Chemin du fichier de sortie anonymisé (optionnel)."),
    log_entities: Optional[Path] = typer.Option(None, "--log-entities", help="Chemin du fichier CSV de log des entités détectées (optionnel)."),
    mapping_output: Optional[Path] = typer.Option(None, "--mapping-output", help="Chemin du fichier CSV du mapping d'anonymisation (optionnel)."),
    output_dir: Path = typer.Option(Path("."), "--output-dir", help="Dossier où écrire les fichiers de sortie par défaut (si les chemins spécifiques ne sont pas fournis).", file_okay=False, dir_okay=True, writable=True, resolve_path=True),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulation sans écriture de fichiers."),
    csv_no_header: bool = typer.Option(False, "--csv-no-header", help="Indique que le fichier CSV d'entrée N'A PAS d'en-tête (utilisé si --has-header-opt n'est pas fourni)."),
    has_header_opt: Optional[str] = typer.Option(None, "--has-header-opt", help="Spécifie explicitement si le fichier CSV d'entrée a une en-tête ('true'/'false'). Prioritaire sur --csv-no-header."),
    exclude_entities: Optional[List[str]] = typer.Option(None, "--exclude-entities", help="Types d'entités à exclure, séparés par des virgules (ex: PER,LOC)."),
    custom_replacements_json: Optional[str] = typer.Option(None, "--custom-replacements-json", help="Chaîne JSON des règles de remplacement personnalisées (ex: '[{\"pattern\": \"Confidentiel\", \"replacement\": \"[SECRET]\"}]')."),
    append_timestamp: bool = typer.Option(True, help="Ajoute un timestamp aux noms des fichiers de sortie par défaut."),
    force: bool = typer.Option(False, "--force", "-f", help="Force l’écrasement des fichiers de sortie existants.")
):
    """
    Anonymise un fichier (texte, CSV, JSON, etc.) en utilisant spaCy et des règles configurables.
    """
    console.display_welcome()
    console.console.print(f"📂 Anonymisation du fichier : [bold cyan]{input_file.name}[/bold cyan]") # Corrected
    
    run_id = timestamp()

    csv_has_header_bool: Optional[bool] = None
    if has_header_opt is not None:
        csv_has_header_bool = has_header_opt.lower() == "true"
    else:
        csv_has_header_bool = not csv_no_header

    try:
        # 1. Charger la configuration effective (fusionnée)
        effective_config = ConfigManager.get_effective_config(config)
        console.console.print("🔧 Configuration chargée et validée.") # Corrected

        # 2. Résolution des chemins de sortie
        path_manager = PathManager(input_file, output_dir, run_id, append_timestamp)
        paths = path_manager.resolve_paths(output, mapping_output, log_entities, dry_run)
        console.console.print("➡️  Chemins de sortie résolus.") # Corrected

        # 3. Vérifications pré-traitement (écrasement de fichiers)
        if not dry_run:
            ValidationManager.check_overwrite([p for p in paths.values() if p.name != "dry_run_output.tmp" and p.name != "dry_run_mapping.tmp" and p.name != "dry_run_log.tmp"], force)
        
        console.console.print("⚙️  Démarrage du traitement d'anonymisation...") # Corrected

        # 4. Traitement principal
        result = process_anonymization(
            input_file=input_file,
            effective_config=effective_config,
            paths=paths,
            dry_run=dry_run,
            exclude_entities_cli=exclude_entities,
            custom_replacements_json=custom_replacements_json,
            csv_has_header=csv_has_header_bool
        )

        # 5. Post-processing et affichage des résultats
        console.display_results(result, dry_run, paths) # This calls a method on console which then uses console.console.print internally

        # 6. Logging centralisé de l'exécution
        log_run_event(
            logger=CLIUsageLogger,
            run_id=run_id,
            input_file=str(input_file),
            output_file=str(paths.get("output_file")) if paths.get("output_file") and not dry_run else "DRY_RUN_NO_OUTPUT",
            mapping_file=str(paths.get("mapping_file")) if paths.get("mapping_file") and not dry_run else "DRY_RUN_NO_MAPPING",
            log_entities_file=str(paths.get("log_entities_file")) if paths.get("log_entities_file") and not dry_run else "DRY_RUN_NO_LOG",
            entities_detected=result.get("entities_detected", []),
            total_replacements=result.get("total_replacements", 0),
            audit_log=result.get("audit_log", []),
            status=result.get("status", "unknown"),
            error=result.get("error")
        )

    except AnonyfilesError as e:
        console.handle_error(e, "anonymize_command") # This calls a method on console which then uses console.console.print internally
        raise typer.Exit(e.exit_code)
    except Exception as e:
        console.handle_error(e, "anonymize_command_unexpected") # This calls a method on console which then uses console.console.print internally
        raise typer.Exit(2)


@app.command()
def deanonymize(
    input_file: Path = typer.Argument(..., help="Fichier à désanonymiser", exists=True, file_okay=True, dir_okay=False, readable=True),
    mapping_csv: Path = typer.Option(..., help="Mapping CSV à utiliser", exists=True, file_okay=True, dir_okay=False, readable=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Fichier de sortie restauré (optionnel)."),
    report: Optional[Path] = typer.Option(None, "--report", help="Fichier de rapport détaillé JSON sur la désanonymisation (optionnel)."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simulation sans écriture de fichiers."),
    permissive: bool = typer.Option(False, "--permissive", help="Tolère les codes inconnus dans le mapping et restaure ce qui peut l'être (mode non-strict).")
):
    """
    Désanonymise un fichier anonymisé à partir d'un mapping CSV.
    """
    console.display_welcome() # This calls a method on console which then uses console.console.print internally
    console.console.print(f"🔁 Désanonymisation du fichier : [bold cyan]{input_file.name}[/bold cyan]") # Corrected
    console.console.print(f"🔗 Fichier de mapping : [bold green]{mapping_csv}[/bold green]") # Corrected

    strict_mode = not permissive
    
    try:
        output_path = output
        if not output_path and not dry_run:
            output_path = input_file.parent / f"{input_file.stem}_deanonymise_{timestamp()}{input_file.suffix}"
            
        report_path = report
        if not report_path and not dry_run and output_path:
            report_path = output_path.parent / f"{input_file.stem}_deanonymise_report_{timestamp()}.json"

        if not dry_run and output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if output_path.exists() and not typer.confirm(f"⚠️ Le fichier de sortie '{output_path}' existe déjà. L'écraser ?"):
                raise typer.Exit(code=1)

        with open(input_file, encoding="utf-8") as f:
            content_to_deanonymize = f.read()

        deanonymizer = Deanonymizer(str(mapping_csv), strict=strict_mode)
        restored_text, report_data = deanonymizer.deanonymize_text(content_to_deanonymize, dry_run=dry_run)

        if not dry_run:
            if output_path:
                output_path.write_text(restored_text, encoding="utf-8")
                console.console.print(f"✅ Fichier restauré avec succès : [bold green]{output_path}[/bold green]") # Corrected
            else:
                console.console.print("INFO: Mode non-dry_run mais aucun fichier de sortie (--output) spécifié. Texte restauré non sauvegardé.") # Corrected
                console.console.print("\n--- Texte restauré (aperçu, max 1000 caractères) ---") # Corrected
                console.console.print(restored_text[:1000] + ("..." if len(restored_text) > 1000 else ""), style="dim")
                console.console.print("---------------------------------------------------") # Corrected

            if report_path:
                report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
                console.console.print(f"📊 Rapport de désanonymisation détaillé sauvegardé : [bold green]{report_path}[/bold green]") # Corrected
            elif not output_path:
                console.console.print("\n--- Rapport de désanonymisation (JSON) ---") # Corrected
                console.console.print(json.dumps(report_data, indent=2, ensure_ascii=False), style="dim")
                console.console.print("----------------------------------------") # Corrected
            
            console.console.print("✅ Désanonymisation terminée.") # Corrected

        else:
            console.console.print(Panel.fit( # Corrected
                "[bold yellow]Simulation de désanonymisation (dry_run) terminée.[/bold yellow]\n"
                f"Fichier d'entrée analysé : [green]{input_file}[/green]\n"
                f"Fichier de mapping utilisé : [green]{mapping_csv}[/green]\n"
                f"Mode strict : [yellow]{strict_mode}[/yellow] (permissif : [yellow]{permissive}[/yellow])",
                border_style="yellow"
            ))
            console.console.print(f"Nombre de codes remplacés (estimé) : [bold]{report_data.get('replacements_successful_count', 'N/A')}[/bold]") # Corrected
            console.console.print(f"Couverture du mapping (estimé) : [bold]{report_data.get('coverage_percentage', 'N/A')}[/bold]") # Corrected
            if report_data.get('warnings_generated_during_deanonymization'):
                console.console.print("⚠️ Avertissements générés pendant la simulation :") # Corrected
                for warning_msg in report_data['warnings_generated_during_deanonymization']:
                    console.console.print(f"  - [yellow]{warning_msg}[/yellow]") # Corrected
            console.console.print("Aucun fichier n'a été écrit.") # Corrected
        
        # Log de l'exécution pour la désanonymisation
        log_run_event(
            logger=CLIUsageLogger,
            run_id=timestamp(),
            input_file=str(input_file),
            output_file=str(output_path) if output_path and not dry_run else "DRY_RUN_NO_OUTPUT",
            mapping_file=str(mapping_csv),
            log_entities_file="",
            entities_detected=report_data.get("distinct_codes_in_text_list", []),
            total_replacements=report_data.get("replacements_successful_count", 0),
            audit_log=report_data.get("warnings_generated_during_deanonymization", []),
            status="success" if not report_data.get("warnings_generated_during_deanonymization") else "success_with_warnings",
            error=None
        )


    except AnonyfilesError as e:
        console.handle_error(e, "deanonymize_command") # This calls a method on console which then uses console.console.print internally
        raise typer.Exit(e.exit_code)
    except Exception as e:
        console.handle_error(e, "deanonymize_command_unexpected") # This calls a method on console which then uses console.console.print internally
        raise typer.Exit(2)


if __name__ == "__main__":
    ConfigManager.create_default_user_config()
    app()