# main.py

import typer
from pathlib import Path
from typing import Optional, List
import yaml

from anonymizer.anonyfiles_core import AnonyfilesEngine

# Import du Typer app du module cli_config
from cli_config import app as config_app

app = typer.Typer(help="Anonymisation automatique de fichiers (.docx, .xlsx, .csv, .txt)")

# Ajout du sous-typer 'config' avec ses commandes
app.add_typer(config_app, name="config")

DEFAULT_CONFIG_PATH = Path("config.yaml.sample")

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
        if "log_file" in result:
            typer.echo(f"Log entités : {result['log_file']}")
    else:
        typer.secho(f"Erreur : {result.get('error', 'Erreur inconnue')}", fg=typer.colors.RED)

if __name__ == "__main__":
    app()
