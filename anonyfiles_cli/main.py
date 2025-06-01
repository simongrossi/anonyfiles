# anonyfiles_cli/main.py

import typer
from pathlib import Path
import json
from typing import Optional, List, Dict # Ajout de Dict pour config_data
# Assurez-vous que CLIUsageLogger est bien importable.
# Si ce fichier n'existe pas ou pose problème, commentez les lignes où il est utilisé.
from cli_logger import CLIUsageLogger
from anonymizer.anonyfiles_core import AnonyfilesEngine
from anonymizer.csv_processor import CsvProcessor
from anonymizer.txt_processor import TxtProcessor
from anonymizer.deanonymize import Deanonymizer
from anonymizer.file_utils import timestamp, ensure_folder, make_run_dir, default_output, default_mapping, default_log
from anonymizer.run_logger import log_run_event
import yaml

app = typer.Typer()

def load_config(config_path: Path) -> dict:
    try:
        with open(str(config_path), encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        typer.echo(f"ERREUR CRITIQUE: Le fichier de configuration '{config_path}' spécifié n'a pas été trouvé lors du chargement.", err=True)
        raise typer.Exit(code=1)
    except yaml.YAMLError as e:
        typer.echo(f"ERREUR CRITIQUE: Erreur lors du parsing du fichier YAML '{config_path}': {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"ERREUR CRITIQUE: Une erreur inattendue est survenue lors du chargement de '{config_path}': {e}", err=True)
        raise typer.Exit(code=1)


def assert_file_exists(path: Path, label: str):
    if not path.is_file():
        typer.echo(f"Erreur : Le fichier {label} '{path}' n'existe pas.", err=True)
        raise typer.Exit(code=1) # Spécifier un code de sortie

def parse_custom_replacements(custom_replacements_json: Optional[str]) -> list:
    """Parse et valide la chaîne JSON des règles custom"""
    if not custom_replacements_json:
        return []
    try:
        parsed = json.loads(custom_replacements_json)
        if isinstance(parsed, list):
            # Idéalement, ajouter une validation plus poussée de la structure de chaque règle ici
            return parsed
        else:
            typer.echo(f"ERREUR: --custom-replacements-json doit être une liste JSON valide. Reçu : {type(parsed)}", err=True)
            raise typer.Exit(code=1) # Quitter si le format n'est pas bon
    except json.JSONDecodeError as e:
        typer.echo(f"ERREUR: JSON invalide pour --custom-replacements-json : {e}", err=True)
        raise typer.Exit(code=1) # Quitter si le JSON est malformé
    return [] # Ne devrait pas être atteint si on quitte en cas d'erreur


@app.command()
def anonymize(
    input_file: Path = typer.Argument(..., help="Fichier à anonymiser", exists=True, file_okay=True, dir_okay=False, readable=True),
    config: Optional[Path] = typer.Option(None, "--config", "-c", help="Fichier de configuration YAML (optionnel). S'il est fourni, il doit exister.", exists=True, file_okay=True, dir_okay=False, readable=True),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Fichier de sortie anonymisé (optionnel)."),
    log_entities: Optional[Path] = typer.Option(None, "--log-entities", help="Fichier CSV de log des entités détectées (optionnel)."),
    mapping_output: Optional[Path] = typer.Option(None, "--mapping-output", help="Fichier CSV du mapping d'anonymisation (optionnel)."),
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
    Si aucun fichier de configuration n'est fourni, des stratégies de remplacement par défaut seront appliquées.
    """
    typer.echo(f"📂 Anonymisation du fichier : {input_file}")

    # assert_file_exists est déjà géré par Typer avec exists=True pour input_file et config

    config_data: Dict[str, Any] = {}
    if config:
        typer.echo(f"🔧 Utilisation du fichier de configuration : {config}")
        config_data = load_config(config) # load_config gère les erreurs de chargement/parsing
    else:
        typer.echo("INFO: Aucun fichier de configuration YAML fourni. Utilisation des stratégies de remplacement par défaut intégrées.")

    run_id_for_outputs = timestamp() # Un seul timestamp pour tous les fichiers d'un run

    # Déterminer les chemins de sortie effectifs
    # Si un chemin est fourni par l'utilisateur, on l'utilise, sinon on le construit.
    # La création du dossier de run est conditionnée au fait qu'au moins un fichier y sera écrit.
    
    run_dir_path: Optional[Path] = None # Initialiser à None
    
    def get_run_dir() -> Path: # Fonction utilitaire pour créer le dossier de run à la demande
        nonlocal run_dir_path
        if run_dir_path is None:
            run_dir_path = make_run_dir(output_dir, run_id_for_outputs)
        return run_dir_path

    effective_output_path = output
    if not output and not dry_run: # On ne génère un chemin par défaut que si on va écrire
        effective_output_path = default_output(input_file, get_run_dir(), append_timestamp)

    effective_mapping_path = mapping_output
    if not mapping_output and not dry_run: # Optionnel, on le crée s'il n'est pas spécifié et pas en dry_run
        effective_mapping_path = default_mapping(input_file, get_run_dir())

    effective_log_entities_path = log_entities
    if not log_entities and not dry_run: # Optionnel
        effective_log_entities_path = default_log(input_file, get_run_dir())

    # Vérification de l'écrasement (uniquement si pas en dry_run)
    if not dry_run:
        paths_to_check_for_overwrite = []
        if effective_output_path: paths_to_check_for_overwrite.append(effective_output_path)
        if effective_mapping_path: paths_to_check_for_overwrite.append(effective_mapping_path)
        if effective_log_entities_path: paths_to_check_for_overwrite.append(effective_log_entities_path)

        for p_check in paths_to_check_for_overwrite:
            # S'assurer que le dossier parent existe avant de vérifier si le fichier existe
            # (surtout pour les chemins spécifiés par l'utilisateur)
            p_check.parent.mkdir(parents=True, exist_ok=True)
            if p_check.exists() and not force:
                typer.echo(f"⚠️  Le fichier de sortie '{p_check}' existe déjà. Utilisez --force pour l’écraser.", err=True)
                raise typer.Exit(1)
    
    # Pour le mode dry_run, si les chemins ne sont pas spécifiés, ils restent None.
    # L'engine devra gérer les chemins None (ne pas essayer d'écrire).
    # Si un chemin est spécifié en dry_run (ex: --output mon_test.txt), effective_output_path sera ce chemin.
    # On peut afficher un message si output est spécifié en dry_run.
    if dry_run and output:
        typer.echo(f"INFO: Mode dry_run. Le fichier de sortie spécifié '{output}' ne sera pas créé.")


    custom_rules_list = parse_custom_replacements(custom_replacements_json)

    engine = AnonyfilesEngine(
        config=config_data,
        exclude_entities_cli=exclude_entities,
        custom_replacement_rules=custom_rules_list
    )

    processor_kwargs = {}
    if input_file.suffix.lower() == ".csv":
        if has_header_opt is not None:
            if has_header_opt.lower() == "true":
                processor_kwargs['has_header'] = True
            elif has_header_opt.lower() == "false":
                processor_kwargs['has_header'] = False
            else:
                typer.echo(f"AVERTISSEMENT: Valeur de --has-header-opt ('{has_header_opt}') non reconnue. Ignorée. Utilisation de --csv-no-header.", err=True)
                processor_kwargs['has_header'] = not csv_no_header # Fallback
        else:
            processor_kwargs['has_header'] = not csv_no_header
        typer.echo(f"DEBUG (main.py): Option CSV has_header déterminée à: {processor_kwargs['has_header']}")

    try:
        result = engine.anonymize(
            input_path=input_file,
            output_path=effective_output_path, # Peut être None si dry_run et non spécifié
            entities=None,
            dry_run=dry_run,
            log_entities_path=effective_log_entities_path, # Peut être None
            mapping_output_path=effective_mapping_path, # Peut être None
            **processor_kwargs
        )

        try:
            log_run_event(
                logger=CLIUsageLogger, # Nom de paramètre corrigé
                run_id=run_id_for_outputs, # Utiliser le timestamp généré
                input_file=str(input_file),
                output_file=str(effective_output_path) if effective_output_path and not dry_run else "DRY_RUN_NO_OUTPUT",
                mapping_file=str(effective_mapping_path) if effective_mapping_path and not dry_run else "DRY_RUN_NO_MAPPING",
                log_entities_file=str(effective_log_entities_path) if effective_log_entities_path and not dry_run else "DRY_RUN_NO_LOG",
                entities_detected=result.get("entities_detected", []),
                total_replacements=result.get("total_replacements", 0),
                audit_log=result.get("audit_log", []),
                status=str(result.get("status", "unknown")), # Fournir une valeur par défaut
                error=str(result.get("error", None)) if result.get("error") else None # Nom de paramètre corrigé
            )
        except Exception as log_e:
            typer.echo(f"AVERTISSEMENT: Échec du logging centralisé de l'exécution : {log_e}", err=True)

        if result.get("status") == "error":
            typer.echo(f"❌ Erreur lors de l'anonymisation : {result.get('error')}", err=True)
            raise typer.Exit(1)

        if not dry_run:
            typer.echo(typer.style("✅ Anonymisation terminée.", fg=typer.colors.GREEN, bold=True))
            if effective_output_path: # Le fichier a été écrit
                typer.echo(f"Fichier anonymisé : {effective_output_path}")
            # Vérifier si les fichiers optionnels ont été effectivement créés par l'engine avant de les annoncer
            if effective_mapping_path and effective_mapping_path.exists():
                typer.echo(f"Mapping CSV : {effective_mapping_path}")
            if effective_log_entities_path and effective_log_entities_path.exists():
                typer.echo(f"Log des entités : {effective_log_entities_path}")
        else:
            typer.echo(typer.style("✅ Simulation d'anonymisation (dry_run) terminée.", fg=typer.colors.YELLOW, bold=True))
            typer.echo(f"Fichier d'entrée analysé : {input_file}")
            typer.echo(f"Entités détectées (estimé) : {len(result.get('entities_detected', []))}")
            typer.echo(f"Remplacements effectués (estimé) : {result.get('total_replacements', 0)}")
            typer.echo("Aucun fichier n'a été écrit.")

    except typer.Exit:
        raise
    except Exception as e:
        try:
            CLIUsageLogger.log_error("main_cli_anonymize_unexpected", e)
        except Exception as log_e_crit:
             typer.echo(f"AVERTISSEMENT: Échec du logging centralisé de l'erreur critique : {log_e_crit}", err=True)
        typer.echo(f"❌ Erreur inattendue lors de l'anonymisation : {e}", err=True)
        import traceback
        typer.echo(f"Traceback:\n{traceback.format_exc()}", err=True)
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
    typer.echo(f"🔁 Désanonymisation du fichier : {input_file}")

    strict_mode = not permissive

    # assert_file_exists est déjà géré par Typer pour input_file et mapping_csv

    try:
        with open(input_file, encoding="utf-8") as f:
            content_to_deanonymize = f.read()
    except Exception as e:
        typer.echo(f"❌ Erreur lors de la lecture du fichier d'entrée '{input_file}': {e}", err=True)
        raise typer.Exit(1)

    deanonymizer = Deanonymizer(str(mapping_csv), strict=strict_mode)
    restored_text, report_data = deanonymizer.deanonymize_text(content_to_deanonymize, dry_run=dry_run)

    if not dry_run:
        if output:
            try:
                output.parent.mkdir(parents=True, exist_ok=True)
                with open(output, "w", encoding="utf-8") as f_out:
                    f_out.write(restored_text)
                typer.echo(f"✅ Fichier restauré avec succès : {output}")
            except Exception as e:
                typer.echo(f"❌ Erreur lors de l'écriture du fichier restauré '{output}': {e}", err=True)
                # Ne pas quitter, on peut toujours afficher le rapport ou le texte
        else:
            typer.echo("INFO: Mode non-dry_run mais aucun fichier de sortie (--output) spécifié. Texte restauré non sauvegardé.")
            typer.echo("\n--- Texte restauré (aperçu, max 1000 caractères) ---")
            typer.echo(restored_text[:1000] + ("..." if len(restored_text) > 1000 else ""))
            typer.echo("---------------------------------------------------")

        if report:
            try:
                report.parent.mkdir(parents=True, exist_ok=True)
                with open(report, "w", encoding="utf-8") as f_report:
                    json.dump(report_data, f_report, indent=2, ensure_ascii=False)
                typer.echo(f"📊 Rapport de désanonymisation détaillé sauvegardé : {report}")
            except Exception as e:
                typer.echo(f"❌ Erreur lors de l'écriture du rapport JSON '{report}': {e}", err=True)
        # Afficher le rapport en console si ni --output ni --report n'est spécifié
        elif not output: # Si on n'a rien écrit sur disque
            typer.echo("\n--- Rapport de désanonymisation (JSON) ---")
            try:
                typer.echo(json.dumps(report_data, indent=2, ensure_ascii=False))
            except Exception: # Au cas où report_data ne serait pas sérialisable, peu probable
                 typer.echo(str(report_data))
            typer.echo("----------------------------------------")

    else: # Si dry_run est True
        typer.echo(typer.style("✅ Simulation de désanonymisation (dry_run) terminée.", fg=typer.colors.YELLOW, bold=True))
        typer.echo(f"Fichier d'entrée analysé : {input_file}")
        typer.echo(f"Fichier de mapping utilisé : {mapping_csv}")
        typer.echo(f"Mode strict : {strict_mode} (permissif : {permissive})")
        typer.echo(f"Nombre de codes remplacés (estimé) : {report_data.get('replaced_count', 'N/A')}")
        typer.echo(f"Couverture du mapping (estimé) : {report_data.get('coverage', 'N/A')}")
        if report_data.get('warnings'):
            typer.echo("Avertissements générés pendant la simulation :")
            for warning_msg in report_data['warnings']: # Renommé pour éviter conflit de nom
                typer.echo(f"  - {warning_msg}")
        typer.echo("Aucun fichier n'a été écrit.")


if __name__ == "__main__":
    typer.echo("anonyfiles CLI (config optionnelle, gestion des runs améliorée)")
    app()