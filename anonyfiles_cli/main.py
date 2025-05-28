# anonyfiles_cli/main.py
import typer
from pathlib import Path
from datetime import datetime
import os
import json
from typing import Optional, List
from cli_logger import CLIUsageLogger
from anonymizer.anonyfiles_core import AnonyfilesEngine
from anonymizer.csv_processor import CsvProcessor
from anonymizer.txt_processor import TxtProcessor
from anonymizer.deanonymize import Deanonymizer
import yaml

app = typer.Typer()

def load_config(config_path: Path) -> dict:
    with open(str(config_path), encoding="utf-8") as f:
        return yaml.safe_load(f)

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def ensure_folder(folder: Path) -> None:
    os.makedirs(folder, exist_ok=True)

def make_run_dir(base_output_dir: Path, run_id: str) -> Path:
    run_dir = base_output_dir / "runs" / run_id
    ensure_folder(run_dir)
    return run_dir

def default_output(input_file: Path, run_dir: Path, append_timestamp: bool) -> Path:
    base = input_file.stem
    ext = input_file.suffix
    filename = f"{base}_anonymise_{timestamp()}{ext}" if append_timestamp else f"{base}_anonymise{ext}"
    return run_dir / filename

def default_mapping(input_file: Path, run_dir: Path) -> Path:
    base = input_file.stem
    return run_dir / f"{base}_mapping_{timestamp()}.csv"

def default_log(input_file: Path, run_dir: Path) -> Path:
    base = input_file.stem
    return run_dir / f"{base}_entities_{timestamp()}.csv"

@app.command()
def anonymize(
    input_file: Path = typer.Argument(..., help="Fichier à anonymiser"),
    config: Path = typer.Option(..., help="Fichier de configuration YAML"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Fichier de sortie anonymisé"),
    log_entities: Optional[Path] = typer.Option(None, help="Fichier CSV de log des entités détectées"),
    mapping_output: Optional[Path] = typer.Option(None, help="Fichier CSV du mapping anonymisation"),
    output_dir: Path = typer.Option(".", "--output-dir", help="Dossier où écrire tous les outputs"),
    dry_run: bool = typer.Option(False, help="Simulation sans écriture de fichiers"),
    csv_no_header: bool = typer.Option(False, help="Le CSV n'a PAS d'entête"),
    has_header_opt: Optional[str] = typer.Option(None, help="Spécifie explicitement si le fichier a une entête ('true'/'false')"),
    exclude_entities: Optional[List[str]] = typer.Option(None, help="Types d'entités à exclure (ex: PER,LOC)"),
    custom_replacements_json: Optional[str] = typer.Option(None, help="Chaîne JSON des règles de remplacement personnalisées"),
    append_timestamp: bool = typer.Option(True, help="Ajoute un timestamp dans les noms de fichiers"),
    force: bool = typer.Option(False, help="Force l’écrasement des fichiers existants")
):
    """
    Anonymise un fichier texte ou CSV.
    """
    typer.echo(f"📂 Anonymisation du fichier : {input_file}")

    if not input_file.is_file():
        typer.echo(f"Erreur : Le fichier d'entrée '{input_file}' n'existe pas.", err=True)
        raise typer.Exit(1)

    if not config.is_file():
        typer.echo(f"Erreur : Le fichier de configuration '{config}' n'existe pas.", err=True)
        raise typer.Exit(1)

    run_id = timestamp()
    run_dir = make_run_dir(output_dir, run_id)

    output = output or default_output(input_file, run_dir, append_timestamp)
    mapping_output = mapping_output or default_mapping(input_file, run_dir)
    log_entities = log_entities or default_log(input_file, run_dir)

    for path in [output, mapping_output, log_entities]:
        if path.exists() and not force:
            typer.echo(f"⚠️ Le fichier {path} existe déjà. Utilisez --force pour l’écraser.", err=True)
            raise typer.Exit(1)

    config_data = load_config(config)
    custom_rules_list = []

    if custom_replacements_json:
        try:
            parsed = json.loads(custom_replacements_json)
            if isinstance(parsed, list):
                custom_rules_list = parsed
            else:
                typer.echo("--custom-replacements-json n'est pas une liste valide.", err=True)
        except json.JSONDecodeError as e:
            typer.echo(f"JSON invalide : {e}", err=True)

    engine = AnonyfilesEngine(
        config=config_data,
        exclude_entities_cli=exclude_entities,
        custom_replacement_rules=custom_rules_list
    )

    processor_kwargs = {}
    if input_file.suffix.lower() == ".csv":
        processor_kwargs['has_header'] = (has_header_opt.lower() == "true") if has_header_opt else not csv_no_header

    try:
        result = engine.anonymize(
            input_path=input_file,
            output_path=output,
            entities=None,
            dry_run=dry_run,
            log_entities_path=log_entities,
            mapping_output_path=mapping_output,
            **processor_kwargs
        )

        CLIUsageLogger.log_run({
            "timestamp": run_id,
            "input_file": str(input_file),
            "output_file": str(output),
            "mapping_file": str(mapping_output),
            "log_entities_file": str(log_entities),
            "entities_detected": result.get("entities_detected", []),
            "total_replacements": result.get("total_replacements", 0),
            "rules_applied": result.get("audit_log", []),
            "success": result.get("status") == "success",
            "error": result.get("error", None)
        })

        if result.get("status") == "error":
            typer.echo(f"❌ Erreur : {result.get('error')}", err=True)
            raise typer.Exit(1)

        typer.echo(typer.style("✅ Anonymisation terminée.", fg=typer.colors.GREEN, bold=True))
        typer.echo(f"Fichier anonymisé : {output}\nMapping CSV : {mapping_output}\nLog des entités : {log_entities}")

    except Exception as e:
        CLIUsageLogger.log_error("main_cli", e)
        typer.echo(f"❌ Erreur inattendue : {e}", err=True)
        raise typer.Exit(2)

@app.command()
def deanonymize(
    input_file: Path = typer.Argument(..., help="Fichier à désanonymiser"),
    mapping_csv: Path = typer.Option(..., help="Mapping CSV à utiliser"),
    output: Optional[Path] = typer.Option(None, help="Fichier de sortie restauré"),
    report: Optional[Path] = typer.Option(None, help="Fichier de rapport détaillé"),
    dry_run: bool = typer.Option(False, help="Simulation sans écriture"),
    permissive: bool = typer.Option(False, help="Tolère les codes inconnus (restaure tout ce qu'on peut)"),
    csv_no_header: bool = typer.Option(False, help="Le CSV n'a PAS d'entête")
):
    """
    Désanonymise un fichier anonymisé à partir d'un mapping CSV.
    """
    typer.echo(f"🔁 Désanonymisation du fichier : {input_file}")

    strict = not permissive

    with open(input_file, encoding="utf-8") as f:
        content = f.read()

    deanonymizer = Deanonymizer(str(mapping_csv), strict=strict)
    result, report_data = deanonymizer.deanonymize_text(content, dry_run=dry_run)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
        typer.echo(f"✅ Fichier restauré : {output}")

    if report:
        with open(report, "w", encoding="utf-8") as f:
            f.write(json.dumps(report_data, indent=2, ensure_ascii=False))
        typer.echo(f"📊 Rapport détaillé : {report}")

if __name__ == "__main__":
    typer.echo("anonyfiles CLI (avec timestamp, --force, runs/)")
    app()
