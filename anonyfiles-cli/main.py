import typer
import os
import csv
import logging
from pathlib import Path
from typing import List, Optional
import importlib.metadata

from anonymizer.spacy_engine import SpaCyEngine
from anonymizer.word_processor import extract_text_from_docx, replace_entities_in_docx
from anonymizer.excel_processor import extract_text_from_excel, replace_entities_in_excel
from anonymizer.csv_processor import extract_text_from_csv, replace_entities_in_csv
from anonymizer.txt_processor import extract_text_from_txt, replace_entities_in_txt
from anonymizer.replacer import generate_replacements

# CLI App
app = typer.Typer(help="Anonymise automatiquement des fichiers Word, Excel, CSV et TXT.")
__version__ = importlib.metadata.version("anonyfiles")

# Configure logging
logger = logging.getLogger("anonyfiles")


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="Afficher la version et quitter.")
):
    """CLI d'anonymisation de documents avec anonyfiles."""
    if version:
        typer.echo(f"anonyfiles version {__version__}")
        raise typer.Exit()


@app.command("anonymize")
def anonymize(
    input_filename: Path = typer.Argument(..., exists=True, file_okay=True, readable=True, help="Fichier à anonymiser (dans input_files/)") ,
    output_filename: Optional[Path] = typer.Option(None, "-o", "--output", help="Chemin de sortie (par défaut output_files/)") ,
    entities: List[str] = typer.Option([], "-e", "--entities", help="Types d'entités à anonymiser (ex: PER LOC ORG DATE EMAIL). Toutes si vide."),
    log_entities: Optional[Path] = typer.Option(None, "-l", "--log-entities", help="Exporter les entités détectées vers un fichier CSV."),
    dry_run: bool = typer.Option(False, "-n", "--dry-run", help="Simule sans écrire de fichier."),
    verbose: bool = typer.Option(False, "--verbose", help="Mode verbeux (debug).")
):
    """Anonymise le fichier spécifié."""
    setup_logging(verbose)
    engine = SpaCyEngine()

    input_path = Path("input_files") / input_filename
    ext = input_filename.suffix.lower()
    output_path = output_filename or (Path("output_files") / f"{input_filename.stem}_anonymise{ext}")

    typer.echo(f"🔍 Lecture de : {input_path}")
    if not input_path.exists():
        typer.secho(f"Erreur : fichier non trouvé {input_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Extraction du texte
    texts: List[str] = []
    if ext == ".docx":
        typer.echo("Traitement Word (.docx)")
        texts = extract_text_from_docx(input_path)
    elif ext == ".xlsx":
        typer.echo("Traitement Excel (.xlsx)")
        texts = extract_text_from_excel(input_path)
    elif ext == ".csv":
        typer.echo("Traitement CSV (.csv)")
        texts = extract_text_from_csv(input_path)
    elif ext == ".txt":
        typer.echo("Traitement TXT (.txt)")
        texts = [extract_text_from_txt(input_path)]
    else:
        typer.secho(f"Type de fichier non supporté : {ext}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Détection
    all_entities = []
    for block in texts:
        ents = engine.detect_entities(block)
        all_entities.extend(ents)
    
    # Filtrage
    if entities:
        selected = set(entities)
        all_entities = [(t, l) for t, l in all_entities if l in selected]
        typer.echo(f"Entités filtrées : {selected}")

    # Export log entités
    if log_entities and all_entities:
        log_path = Path("log") / log_entities
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Entite", "Label"])
            for t, l in all_entities:
                writer.writerow([t, l])
        typer.echo(f"✅ Entités exportées vers {log_path}")

    if not all_entities:
        typer.echo("Aucune entité détectée.")
        raise typer.Exit()

    typer.echo(f"Entités détectées: {all_entities}")
    replacements = generate_replacements(all_entities)
    typer.echo(f"Remplacements générés: {replacements}")

    if dry_run:
        typer.echo("--dry-run: aucun fichier de sortie généré.")
        raise typer.Exit()

    # Application des remplacements
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if ext == ".docx":
        replace_entities_in_docx(input_path, output_path, replacements)
    elif ext == ".xlsx":
        replace_entities_in_excel(input_path, output_path, replacements)
    elif ext == ".csv":
        replace_entities_in_csv(input_path, output_path, replacements)
    elif ext == ".txt":
        replace_entities_in_txt(input_path, output_path, replacements)

    typer.secho(f"✅ Anonymisation terminée: {output_path}", fg=typer.colors.GREEN)


@app.command("list-entities")
def list_entities(
    model: str = typer.Option("fr_core_news_md", "-m", "--model", help="Modèle spaCy à utiliser.")
):
    """Liste les types d'entités reconnus par le modèle spaCy."""
    import spacy
    nlp = spacy.load(model)
    labels = nlp.get_pipe("ner").labels
    for label in labels:
        typer.echo(label)


if __name__ == "__main__":
    app()
