import typer
from pathlib import Path
import json
import yaml
import os
import sys
from typing import Optional, List, Dict, Any
from rich.panel import Panel
from datetime import datetime
import time

# Importation conditionnelle de chardet
try:
    from chardet.universaldetector import UniversalDetector
    has_chardet = True
except ImportError:
    has_chardet = False

# Assurez-vous que CLIUsageLogger est bien importable.
from .cli_logger import CLIUsageLogger

# Imports depuis les modules de votre projet
from .anonymizer.anonyfiles_core import AnonyfilesEngine
from .anonymizer.deanonymize import Deanonymizer
from .anonymizer.run_logger import log_run_event
from .anonymizer.file_utils import timestamp

from .managers.path_manager import PathManager
from .managers.validation_manager import ValidationManager
from .managers.config_manager import ConfigManager # Importation de ConfigManager
from .exceptions import AnonyfilesError, ConfigurationError, ProcessingError, FileIOError
from .ui.console_display import ConsoleDisplay

app = typer.Typer(pretty_exceptions_show_locals=False)
console = ConsoleDisplay()

# --- Exit codes centralisés ---
class ExitCodes:
    SUCCESS = 0
    USER_CANCEL = 1
    GENERAL_ERROR = 2
    CONFIG_ERROR = 3
    PROCESSING_ERROR = 4

# --- Fonctions utilitaires internes ---
def _open_file_in_editor(file_path: Path):
    """Ouvre un fichier dans l'éditeur de texte par défaut du système."""
    if sys.platform == "win32":
        os.startfile(file_path)
    elif sys.platform == "darwin": # macOS
        typer.launch(str(file_path))
    else: # linux
        try:
            typer.launch(str(file_path))
        except Exception:
            console.console.print(f"Impossible d'ouvrir le fichier avec xdg-open. Veuillez ouvrir manuellement : {file_path}", style="yellow")


# --- Validation centrale des entrées ---
def validate_cli_inputs(
    input_file: Path,
    output: Optional[Path],
    custom_replacements_json: Optional[str],
    csv_no_header: bool,
    has_header_opt: Optional[str]
):
    supported_exts = {".txt", ".csv", ".docx", ".xlsx", ".pdf", ".json"}
    if input_file.suffix.lower() not in supported_exts:
        console.console.print(f"[bold red]Erreur : extension non supportée : {input_file.suffix}[/bold red]")
        raise typer.Exit(code=ExitCodes.CONFIG_ERROR)
    if csv_no_header and input_file.suffix.lower() != ".csv":
        console.console.print(f"[bold red]Erreur : --csv-no-header ne peut être utilisé que pour les fichiers CSV.[/bold red]")
        raise typer.Exit(code=ExitCodes.CONFIG_ERROR)
    if custom_replacements_json:
        try:
            json.loads(custom_replacements_json)
        except Exception as e:
            console.console.print(f"[bold red]Erreur de format JSON pour --custom-replacements-json : {e}[/bold red]")
            raise typer.Exit(code=ExitCodes.CONFIG_ERROR)
    if has_header_opt and has_header_opt.lower() not in ("true", "false"):
        console.console.print("[bold red]Erreur : --has-header-opt doit être 'true' ou 'false'[/bold red]")
        raise typer.Exit(code=ExitCodes.CONFIG_ERROR)

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
    # ----------- AJOUT : validation centrale des entrées -----------
    validate_cli_inputs(
        input_file=input_file,
        output=output,
        custom_replacements_json=custom_replacements_json,
        csv_no_header=csv_no_header,
        has_header_opt=has_header_opt
    )
    # ---------------------------------------------------------------

    console.display_welcome()
    console.console.print(f"📂 Anonymisation du fichier : [bold cyan]{input_file.name}[/bold cyan]")

    run_id = timestamp()

    csv_has_header_bool: Optional[bool] = None
    if has_header_opt is not None:
        csv_has_header_bool = has_header_opt.lower() == "true"
    else:
        csv_has_header_bool = not csv_no_header

    try:
        # 1. Charger la configuration effective (fusionnée)
        effective_config = ConfigManager.get_effective_config(config)
        console.console.print("🔧 Configuration chargée et validée.")

        # 2. Résolution des chemins de sortie
        path_manager = PathManager(input_file, output_dir, run_id, append_timestamp)
        paths = path_manager.resolve_paths(output, mapping_output, log_entities, dry_run)
        console.console.print("➡️  Chemins de sortie résolus.")

        # 3. Vérifications pré-traitement (écrasement de fichiers)
        if not dry_run:
            ValidationManager.check_overwrite([p for p in paths.values() if p.name != "dry_run_output.tmp" and p.name != "dry_run_mapping.tmp" and p.name != "dry_run_log.tmp"], force)
        
        console.console.print("⚙️  Démarrage du traitement d'anonymisation...")

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
        console.display_results(result, dry_run, paths)

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
        console.handle_error(e, "anonymize_command")
        raise typer.Exit(e.exit_code)
    except Exception as e:
        console.handle_error(e, "anonymize_command_unexpected")
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
    console.display_welcome()
    console.console.print(f"🔁 Désanonymisation du fichier : [bold cyan]{input_file.name}[/bold cyan]")
    console.console.print(f"🔗 Fichier de mapping : [bold green]{mapping_csv}[/bold green]")

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
                console.console.print(f"✅ Fichier restauré avec succès : [bold green]{output_path}[/bold green]")
            else:
                console.console.print("INFO: Mode non-dry_run mais aucun fichier de sortie (--output) spécifié. Texte restauré non sauvegardé.")
                console.console.print("\n--- Texte restauré (aperçu, max 1000 caractères) ---")
                console.console.print(restored_text[:1000] + ("..." if len(restored_text) > 1000 else ""), style="dim")
                console.console.print("---------------------------------------------------")

            if report_path:
                report_path.write_text(json.dumps(report_data, indent=2, ensure_ascii=False), encoding="utf-8")
                console.console.print(f"📊 Rapport de désanonymisation détaillé sauvegardé : [bold green]{report_path}[/bold green]")
            elif not output_path:
                console.console.print("\n--- Rapport de désanonymisation (JSON) ---")
                console.console.print(json.dumps(report_data, indent=2, ensure_ascii=False), style="dim")
                console.console.print("----------------------------------------")
            
            console.console.print("✅ Désanonymisation terminée.")

        else:
            console.console.print(Panel.fit(
                "[bold yellow]Simulation de désanonymisation (dry_run) terminée.[/bold yellow]\n"
                f"Fichier d'entrée analysé : [green]{input_file}[/green]\n"
                f"Fichier de mapping utilisé : [green]{mapping_csv}[/green]\n"
                f"Mode strict : [yellow]{strict_mode}[/yellow] (permissif : [yellow]{permissive}[/yellow])",
                border_style="yellow"
            ))
            console.console.print(f"Nombre de codes remplacés (estimé) : [bold]{report_data.get('replacements_successful_count', 'N/A')}[/bold]")
            console.console.print(f"Couverture du mapping (estimé) : [bold]{report_data.get('coverage_percentage', 'N/A')}[/bold]")
            if report_data.get('warnings_generated_during_deanonymization'):
                console.console.print("⚠️ Avertissements générés pendant la simulation :")
                for warning_msg in report_data['warnings_generated_during_deanonymization']:
                    console.console.print(f"  - [yellow]{warning_msg}[/yellow]")
            console.console.print("Aucun fichier n'a été écrit.")
        
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
        console.handle_error(e, "deanonymize_command")
        raise typer.Exit(e.exit_code)
    except Exception as e:
        console.handle_error(e, "deanonymize_command_unexpected")
        raise typer.Exit(2)

@app.command()
def version():
    """Affiche la version d'Anonyfiles"""
    console.console.print("🔧 [bold]Anonyfiles CLI[/bold] - Version 1.0.0")
    console.console.print("Outil d'anonymisation de fichiers basé sur spaCy")
    console.console.print("📚 Documentation: https://github.com/simongrossi/anonyfiles")

@app.command()
def validate_config(
    config_path: Path = typer.Argument(..., help="Fichier de configuration à valider", exists=True)
):
    """Valide un fichier de configuration YAML sans traitement"""
    try:
        config_data = ConfigManager.get_effective_config(config_path)
        console.console.print("✅ Configuration valide !")
        console.console.print(json.dumps(config_data, indent=2, ensure_ascii=False))
    except ConfigurationError as e:
        console.console.print(f"❌ Configuration invalide : {e}", style="red")
        raise typer.Exit(ExitCodes.CONFIG_ERROR)

@app.command()
def list_entities():
    """Liste les types d'entités supportées par spaCy"""
    entities = {
        "PER": "Personnes (noms, prénoms)",
        "ORG": "Organisations (entreprises, institutions)",
        "LOC": "Lieux (villes, pays, adresses)",
        "MISC": "Divers (codes, références)",
        "DATE": "Dates et heures",
        "EMAIL": "Adresses email",
        "PHONE": "Numéros de téléphone",
        "URL": "URLs et liens web"
    }
    
    console.console.print("📋 [bold]Types d'entités supportées:[/bold]")
    for code, desc in entities.items():
        console.console.print(f"  • [cyan]{code}[/cyan]: {desc}")

@app.command()
def info(
    input_file: Path = typer.Argument(..., help="Fichier à analyser", exists=True)
):
    """Affiche des informations détaillées sur un fichier sans le traiter"""
    console.console.print(f"📋 [bold]Analyse de : {input_file.name}[/bold]")
    
    # Informations basiques
    stat = input_file.stat()
    size_mb = stat.st_size / (1024 * 1024)
    
    console.console.print(f"📁 Taille : {stat.st_size:,} octets ({size_mb:.2f} MB)")
    console.console.print(f"📄 Extension : {input_file.suffix}")
    console.console.print(f"📅 Modifié : {datetime.fromtimestamp(stat.st_mtime)}")
    
    # Aperçu du contenu avec détection d'encodage
    content = ""
    if has_chardet:
        detector = UniversalDetector()
        with open(input_file, 'rb') as f:
            for line in f:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
        encoding = detector.result['encoding'] if detector.result and detector.result['encoding'] else 'utf-8'
        console.console.print(f"🔤 Encodage détecté (chardet) : {encoding}")
    else:
        encoding = 'utf-8'
        console.console.print(f"🔤 Encodage supposé : {encoding} (installez 'chardet' pour une détection automatique)")

    try:
        with open(input_file, 'r', encoding=encoding) as f:
            content = f.read(1000)  # Premier Ko
            lines = content.count('\n') + 1
            
        console.console.print(f"📝 Lignes (approx.) : {lines}")
        
        # Aperçu sécurisé
        preview = content[:200] + "..." if len(content) > 200 else content
        console.console.print(f"\n📖 [dim]Aperçu :[/dim]\n{preview}")
        
    except UnicodeDecodeError:
        console.console.print("⚠️ Fichier binaire ou encodage non-UTF8/détecté. Impossible d'afficher l'aperçu textuel.", style="yellow")
    except Exception as e:
        console.console.print(f"❌ Erreur de lecture : {e}", style="red")

@app.command()
def batch(
    input_dir: Path = typer.Argument(..., help="Dossier contenant les fichiers à traiter"),
    pattern: str = typer.Option("*", "--pattern", help="Pattern de fichiers (ex: *.txt, *.csv)"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", help="Dossier de sortie"),
    config: Optional[Path] = typer.Option(None, "--config", help="Configuration commune"),
    dry_run: bool = typer.Option(True, "--dry-run/--no-dry-run", help="Mode simulation"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Recherche récursive")
):
    """Traite plusieurs fichiers en lot"""
    
    if not input_dir.exists() or not input_dir.is_dir():
        console.console.print("❌ Le dossier d'entrée n'existe pas", style="red")
        raise typer.Exit(ExitCodes.GENERAL_ERROR)
    
    # Recherche des fichiers
    if recursive:
        files = list(input_dir.rglob(pattern))
    else:
        files = list(input_dir.glob(pattern))
    
    # Filtrer les fichiers supportés
    supported_extensions = {'.txt', '.csv', '.json', '.docx', '.xlsx', '.pdf'}
    files = [f for f in files if f.suffix.lower() in supported_extensions and f.is_file()]
    
    if not files:
        console.console.print(f"❌ Aucun fichier trouvé avec le pattern '{pattern}' dans '{input_dir}'", style="yellow")
        return
    
    console.console.print(f"🔄 [bold]{len(files)} fichiers trouvés[/bold]")
    
    if not dry_run and not typer.confirm(f"Traiter {len(files)} fichiers ?"):
        return
    
    # Configuration de sortie
    if not output_dir:
        output_dir = input_dir / "anonymized_output"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Traitement batch
    success_count = 0
    error_count = 0
    
    for i, file_path in enumerate(files, 1):
        try:
            console.console.print(f"[{i}/{len(files)}] 📄 {file_path.name}...")
            
            # Réutilise la logique d'anonymisation existante
            effective_config = ConfigManager.get_effective_config(config)
            
            # Génération des chemins de sortie
            rel_path = file_path.relative_to(input_dir)
            output_file = output_dir / rel_path
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Pour le mode batch, les fichiers log et mapping sont optionnels et générés à côté de l'output
            log_entities_file = output_file.parent / f"{output_file.stem}_entities.csv"
            mapping_file = output_file.parent / f"{output_file.stem}_mapping.csv"

            paths_for_batch = {
                "output_file": output_file,
                "log_entities_file": log_entities_file,
                "mapping_file": mapping_file
            }

            # Traitement avec les paramètres par défaut (pas de has_header défini explicitement ici pour le batch)
            # Vous pourriez ajouter une option `--csv-has-header-batch` si nécessaire.
            result = process_anonymization(
                input_file=file_path,
                effective_config=effective_config,
                paths=paths_for_batch,
                dry_run=dry_run,
                exclude_entities_cli=None,
                custom_replacements_json=None,
                csv_has_header=None
            )
            
            if result.get("status") == "success":
                success_count += 1
                console.console.print(f"  ✅ Traité avec succès -> [green]{output_file.relative_to(output_dir.parent)}[/green]", style="green")
            else:
                error_count += 1
                console.console.print(f"  ❌ Erreur : {result.get('error', 'Inconnue')} sur {file_path.name}", style="red")
                
        except Exception as e:
            error_count += 1
            console.console.print(f"  ❌ Erreur inattendue : {e} sur {file_path.name}", style="red")
    
    # Résumé
    console.console.print(f"\n📊 [bold]Résumé du traitement batch:[/bold]")
    console.console.print(f"✅ Succès : [green]{success_count}[/green]")
    console.console.print(f"❌ Erreurs : [red]{error_count}[/red]")
    console.console.print(f"📁 Dossier de sortie : [blue]{output_dir}[/blue]")

@app.command(name="config")
def config_cmd(
    action: str = typer.Argument(..., help="Action: show, edit, reset, create"),
    key: Optional[str] = typer.Option(None, "--key", help="Clé de configuration spécifique (pour 'show')"),
    value: Optional[str] = typer.Option(None, "--value", help="Valeur à définir (pour 'set', non implémenté ici)")
):
    """Gère la configuration d'Anonyfiles"""
    
    user_config_path = ConfigManager.DEFAULT_USER_CONFIG_FILE # Utilisation de l'attribut directement
    
    if action == "show":
        try:
            config_data = ConfigManager.get_effective_config(None) # Pas de CLI config pour 'show'
            if key:
                if key in config_data:
                    console.console.print(f"{key}: {config_data[key]}")
                else:
                    console.console.print(f"❌ Clé '{key}' non trouvée dans la configuration effective.", style="red")
            else:
                console.console.print("🔧 [bold]Configuration actuelle effective (fusionnée):[/bold]")
                console.console.print(json.dumps(config_data, indent=2, ensure_ascii=False))
                
                if user_config_path.exists():
                    console.console.print(f"\n[dim]Fichier de configuration utilisateur : {user_config_path}[/dim]")
                else:
                    console.console.print(f"\n[dim]Aucun fichier de configuration utilisateur trouvé. La configuration par défaut est utilisée.[/dim]")
        except Exception as e:
            console.console.print(f"❌ Erreur de lecture de config : {e}", style="red")
    
    elif action == "create":
        if user_config_path.exists() and not typer.confirm(f"⚠️ Le fichier de configuration '{user_config_path}' existe déjà. L'écraser pour recréer une config par défaut ?"):
            raise typer.Exit(ExitCodes.USER_CANCEL)
        
        try:
            ConfigManager.create_default_user_config()
            console.console.print(f"✅ Configuration par défaut créée dans : {user_config_path}")
        except Exception as e:
            console.console.print(f"❌ Erreur lors de la création de la configuration par défaut : {e}", style="red")
            raise typer.Exit(ExitCodes.CONFIG_ERROR)
    
    elif action == "reset":
        if user_config_path.exists():
            if typer.confirm(f"⚠️ Réinitialiser la configuration utilisateur ({user_config_path}) à ses valeurs par défaut ? Cela supprimera le fichier existant."):
                try:
                    os.remove(user_config_path)
                    ConfigManager.create_default_user_config() # Recrée une version par défaut
                    console.console.print("✅ Configuration utilisateur réinitialisée.")
                except Exception as e:
                    console.console.print(f"❌ Erreur lors de la réinitialisation : {e}", style="red")
                    raise typer.Exit(ExitCodes.CONFIG_ERROR)
            else:
                console.console.print("Opération de réinitialisation annulée.", style="yellow")
                raise typer.Exit(ExitCodes.USER_CANCEL)
        else:
            console.console.print(f"ℹ️ Aucun fichier de configuration utilisateur à réinitialiser. Création d'une config par défaut.", style="blue")
            try:
                ConfigManager.create_default_user_config()
                console.console.print(f"✅ Configuration par défaut créée dans : {user_config_path}")
            except Exception as e:
                console.console.print(f"❌ Erreur lors de la création de la configuration par défaut : {e}", style="red")
                raise typer.Exit(ExitCodes.CONFIG_ERROR)
    
    elif action == "edit":
        if not user_config_path.exists():
            console.console.print(f"ℹ️ Le fichier de configuration utilisateur n'existe pas. Création d'un fichier par défaut pour édition.", style="blue")
            try:
                ConfigManager.create_default_user_config()
                console.console.print(f"✅ Fichier de configuration par défaut créé : {user_config_path}", style="green")
            except Exception as e:
                console.console.print(f"❌ Erreur lors de la création du fichier pour édition : {e}", style="red")
                raise typer.Exit(ExitCodes.CONFIG_ERROR)
                
        console.console.print(f"💡 Ouverture du fichier de configuration pour édition : [blue]{user_config_path}[/blue]")
        _open_file_in_editor(user_config_path)
    
    else:
        console.console.print(f"❌ Action inconnue : [red]{action}[/red]", style="red")
        console.console.print("Actions disponibles : [green]show, edit, reset, create[/green]")
        raise typer.Exit(ExitCodes.GENERAL_ERROR)

@app.command()
def benchmark(
    test_file: Path = typer.Argument(..., help="Fichier de test", exists=True),
    iterations: int = typer.Option(3, "--iterations", "-i", help="Nombre d'itérations"),
    config: Optional[Path] = typer.Option(None, "--config", help="Configuration à tester")
):
    """Teste les performances d'anonymisation"""
    
    console.console.print(f"🚀 [bold]Benchmark d'anonymisation[/bold]")
    console.console.print(f"📄 Fichier : {test_file.name}")
    console.console.print(f"🔄 Itérations : {iterations}")
    
    times = []
    
    for i in range(iterations):
        console.console.print(f"[{i+1}/{iterations}] Traitement...")
        
        start_time = time.time()
        
        try:
            effective_config = ConfigManager.get_effective_config(config)
            
            result = process_anonymization(
                input_file=test_file,
                effective_config=effective_config,
                paths={}, # Pas de fichiers de sortie réels en mode dry_run
                dry_run=True,  # Mode dry_run pour éviter l'écriture et ne mesurer que le traitement
                exclude_entities_cli=None,
                custom_replacements_json=None,
                csv_has_header=None
            )
            
            end_time = time.time()
            duration = end_time - start_time
            times.append(duration)
            
            console.console.print(f"  ⏱️ {duration:.2f}s - {result.get('total_replacements', 0)} remplacements")
            
        except Exception as e:
            console.console.print(f"  ❌ Erreur : {e}", style="red")
    
    if times:
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        console.console.print(f"\n📊 [bold]Résultats:[/bold]")
        console.console.print(f"⏱️ Temps moyen : [cyan]{avg_time:.2f}s[/cyan]")
        console.console.print(f"🚀 Plus rapide : [green]{min_time:.2f}s[/green]")
        console.console.print(f"🐌 Plus lent : [red]{max_time:.2f}s[/red]")

@app.callback()
def main_callback():
    """
    Fonction de rappel principale.
    S'assure qu'un fichier de configuration utilisateur par défaut existe au démarrage de l'application
    s'il n'est pas déjà présent.
    """
    # Utilisation directe de l'attribut DEFAULT_USER_CONFIG_FILE
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