# main.py

import typer
from pathlib import Path
from typing import Optional, List
import yaml
import csv
import re

from anonymizer.anonyfiles_core import AnonyfilesEngine

app = typer.Typer(help="Anonymisation automatique de fichiers (.docx, .xlsx, .csv, .txt)")

DEFAULT_CONFIG_PATH = Path("config.yaml.sample")
DEFAULT_MAPPING_PATH = Path("mappings/mapping.csv")


def load_config(config_path: Optional[Path]):
    if config_path is not None and config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    elif DEFAULT_CONFIG_PATH.exists():
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        return {}


@app.command()
def anonymize(
    input_file: Path = typer.Argument(..., exists=True, help="Fichier à anonymiser"),
    output_file: Optional[Path] = typer.Option(None, "-o", "--output", help="Fichier de sortie"),
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Fichier de configuration YAML"),
    entities: Optional[List[str]] = typer.Option(None, "-e", "--entities", help="Types d'entités à anonymiser (PER, LOC, ORG, DATE, EMAIL...)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simule sans écrire le fichier"),
    log_entities: Optional[Path] = typer.Option(None, "-l", "--log-entities", help="CSV des entités détectées"),
    mapping_output: Optional[Path] = typer.Option(None, "--mapping-output", help="CSV mapping code PER <-> nom original"),
    exclude_entities: Optional[List[str]] = typer.Option(None, "--exclude-entity", help="Exclure une entité sous la forme Texte,Label (ex: Date,PER). Peut être spécifié plusieurs fois."),
):
    """
    Anonymise le fichier spécifié (txt, docx, csv, xlsx) selon la configuration.
    """
    config = load_config(config_path) or {}

    engine = AnonyfilesEngine(config, exclude_entities_cli=exclude_entities)
    ext = input_file.suffix.lower()
    if not output_file:
        output_dir = Path("output_files")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{input_file.stem}_anonymise{ext}"

    if not mapping_output:
        mapping_output = DEFAULT_MAPPING_PATH
    mapping_output.parent.mkdir(parents=True, exist_ok=True)

    if log_entities:
        log_entities.parent.mkdir(parents=True, exist_ok=True)

    result = engine.anonymize(
        input_path=input_file,
        output_path=output_file,
        entities=entities,
        dry_run=dry_run,
        log_entities_path=log_entities,
        mapping_output_path=mapping_output,
    )

    if result["status"] == "success":
        typer.echo(f"✅ Fichier anonymisé : {result.get('output_path', output_file)}")
        if "entities_detected" in result:
            typer.echo(f"Entités détectées : {len(result['entities_detected'])}")
        if "mapping_file" in result:
            typer.echo(f"Mapping PER : {result['mapping_file']}")
        else:
            # Afficher chemin mapping généré si pas dans result
            typer.echo(f"Mapping PER : {mapping_output}")
        if "log_file" in result:
            typer.echo(f"Log entités : {result['log_file']}")
    else:
        typer.secho(f"Erreur : {result.get('error', 'Erreur inconnue')}", fg=typer.colors.RED)


@app.command()
def deanonymize(
    input_file: Path = typer.Argument(..., exists=True, help="Fichier anonymisé à restaurer"),
    mapping_csv: Optional[Path] = typer.Option(None, "--mapping-csv", "-m", help="CSV mapping code <-> nom original"),
    output_file: Optional[Path] = typer.Option(None, "-o", "--output", help="Fichier désanonymisé de sortie"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Simule sans écrire le fichier"),
):
    """
    Désanonymise un fichier texte en remplaçant les codes par leurs noms originaux via un mapping CSV.
    """
    if not mapping_csv:
        mapping_csv = DEFAULT_MAPPING_PATH
    if not mapping_csv.exists():
        typer.secho(f"❌ Fichier mapping CSV introuvable : {mapping_csv}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    mapping = {}
    with open(mapping_csv, newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) >= 2:
                code, original = row[0], row[1]
                mapping[code] = original

    text = input_file.read_text(encoding="utf-8")

    pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in mapping.keys()) + r")\b")

    def replace_code(match):
        code = match.group(0)
        return mapping.get(code, code)

    restored_text = pattern.sub(replace_code, text)

    if dry_run:
        typer.echo("=== Contenu désanonymisé (dry run) ===")
        typer.echo(restored_text)
        return

    if not output_file:
        output_file = Path("output_files") / f"{input_file.stem}_restored{input_file.suffix}"
        output_file.parent.mkdir(exist_ok=True)

    output_file.write_text(restored_text, encoding="utf-8")
    typer.echo(f"✅ Fichier désanonymisé sauvegardé : {output_file}")


if __name__ == "__main__":
    app()
