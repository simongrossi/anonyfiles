# main.py
import typer
import os
import csv
import logging
from pathlib import Path
from typing import List, Optional
import importlib.metadata
import re # Import the 're' module

from anonymizer.spacy_engine import SpaCyEngine, EMAIL_REGEX # Import SpaCyEngine and EMAIL_REGEX
from anonymizer.word_processor import extract_text_from_docx, replace_entities_in_docx
from anonymizer.excel_processor import extract_text_from_excel, replace_entities_in_excel
# Import the modified txt_processor which uses positional replacement
from anonymizer.txt_processor import extract_text_from_txt, replace_entities_in_txt
from anonymizer.csv_processor import extract_text_from_csv, replace_entities_in_csv
from anonymizer.replacer import generate_replacements

# CLI App
app = typer.Typer(help="Anonymise automatiquement des fichiers Word, Excel, CSV et TXT.")

try:
    # This will attempt to get the version if installed as a package
    __version__ = importlib.metadata.version("anonyfiles")
except importlib.metadata.PackageNotFoundError:
    # Fallback if not installed as a package (e.g., running directly)
    __version__ = "0.1.0" # Or some other default version

# Configure logging
logger = logging.getLogger("anonyfiles")


def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

# Initialize SpaCyEngine once when the script starts
# This loads the default model (fr_core_news_md)
# Moved initialization here to avoid reloading on each command call
engine = SpaCyEngine()

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
    # Removed exists=True validation here, as the script constructs the path
    input_filename: Path = typer.Argument(..., file_okay=True, readable=True, help="Fichier à anonymiser (dans input_files/)") ,
    output_filename: Optional[Path] = typer.Option(None, "-o", "--output", help="Chemin de sortie (par défaut output_files/)") ,
    entities: List[str] = typer.Option([], "-e", "--entities", help="Types d'entités à anonymiser (ex: PER LOC ORG DATE EMAIL). Toutes si vide."),
    log_entities: Optional[Path] = typer.Option(None, "-l", "--log-entities", help="Exporter les entités détectées vers un fichier CSV."),
    dry_run: bool = typer.Option(False, "-n", "--dry-run", help="Simule sans écrire de fichier."),
    verbose: bool = typer.Option(False, "--verbose", help="Mode verbeux (debug).")
):
    """Anonymise le fichier spécifié."""
    setup_logging(verbose)
    # engine = SpaCyEngine() # Removed from here

    # Construct the full input path by joining the 'input_files' directory with the provided filename
    input_path = Path("input_files") / input_filename

    # Extract the file extension and convert to lowercase
    ext = input_filename.suffix.lower() # Define 'ext' here

    # Calculate output path based on option or default BEFORE checks that might return
    output_path = output_filename or (Path("output_files") / f"{input_filename.stem}_anonymise{ext}") # Ensure this line is present and here

    typer.echo(f"🔍 Lecture de : {input_path}")
    # Now perform the existence check after constructing the correct path
    if not input_path.exists():
        typer.secho(f"Erreur : fichier non trouvé {input_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # Extraction du texte et détection des entités avec et sans offsets
    texts: List[str] = []
    all_entities_for_replacement_generation = [] # For global replacement generation (text, label)
    entities_per_block_with_offsets = [] # For positional replacement (text, label, start, end)

    if ext == ".docx":
        typer.echo("Traitement Word (.docx)")
        texts = extract_text_from_docx(input_path)
        # For DOCX, need to detect entities per paragraph with offsets later
        # and add (text, label) to all_entities_for_replacement_generation
        # For now, placeholder:
        entities_per_block_with_offsets = [[] for _ in texts] # Placeholder for now

    elif ext == ".xlsx":
        typer.echo("Traitement Excel (.xlsx)")
        texts = extract_text_from_excel(input_path)
        # For XLSX, need to detect entities per cell with offsets later
        # For now, placeholder:
        entities_per_block_with_offsets = [[] for _ in texts] # Placeholder for now


    elif ext == ".csv":
        typer.echo("Traitement CSV (.csv)")
        texts = extract_text_from_csv(input_path)
         # For CSV, need to detect entities per cell with offsets later
         # For now, placeholder:
        entities_per_block_with_offsets = [[] for _ in texts] # Placeholder for now

    elif ext == ".txt":
        typer.echo("Traitement TXT (.txt)")
        text_content = extract_text_from_txt(input_path)
        texts = [text_content] # Store the text in a list

        # --- Detect entities *with offsets* for the TXT block ---
        if text_content.strip():
             doc = engine.nlp(text_content)
             # Store entities with offsets for positional replacement
             block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
             entities_per_block_with_offsets.append(block_entities_with_offsets)

             # --- Also collect entities (without offsets) for global replacement generation ---
             # Include SpaCy entities
             all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
             # Include EMAIL entities detected by regex
             email_matches = re.findall(EMAIL_REGEX, text_content)
             all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])

        else:
             entities_per_block_with_offsets.append([]) # Empty block, no entities

    else: # Type de fichier non supporté
        typer.secho(f"Type de fichier non supporté : {ext}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


    # --- Collect all entities (without offsets) for *global* replacement generation for other file types ---
    # This loop is needed if we process other file types. For TXT, we already collected above.
    # If we were to fully refactor using collect_and_anonymize_text_blocks, this section would change.
    # Leaving it here for now as a placeholder for other file types.
    # if ext != ".txt":
    #     for block in texts: # texts already populated for other types
    #         if isinstance(block, str) and block.strip():
    #              doc = engine.nlp(block)
    #              all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
    #              email_matches = re.findall(EMAIL_REGEX, block)
    #              all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])
    #              # Note: For other file types, entities_per_block_with_offsets is still empty lists here.

    # --- Filtering entities based on selected types ---
    if entities:
        selected = set(entities)
        # Filter the global list of entities before generating replacements
        all_entities_for_replacement_generation = [(t, l) for t, l in all_entities_for_replacement_generation if l in selected]
        typer.echo(f"Entités filtrées : {selected}")


    if not all_entities_for_replacement_generation:
        typer.echo("Aucune entité détectée selon les critères spécifiés.")
        return

    # --- Generate *global* replacements based on unique filtered entities ---
    unique_entities = list(set(all_entities_for_replacement_generation))
    typer.echo(f"Entités uniques détectées: {unique_entities}")

    replacements = generate_replacements(unique_entities)
    typer.echo(f"Remplacements générés: {replacements}")

    # --- Export detected entities log ---
    if log_entities and all_entities_for_replacement_generation:
         log_path = Path("log") / log_entities
         log_path.parent.mkdir(parents=True, exist_ok=True)
         with open(log_path, "w", newline="", encoding="utf-8") as f:
             writer = csv.writer(f)
             writer.writerow(["Entite", "Label"])
             # Log the unique entities that were detected/filtered
             for t, l in unique_entities:
                 writer.writerow([t, l])
         typer.echo(f"✅ Entités exportées vers {log_path}")


    if dry_run:
        typer.echo("--dry-run: aucun fichier de sortie généré.")
        return

    # --- Application des remplacements ---
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if ext == ".docx":
        # This part still uses the old replacement logic - needs update
        replace_entities_in_docx(input_path, output_path, replacements)
    elif ext == ".xlsx":
        # This part still uses the old replacement logic - needs update
        replace_entities_in_excel(input_path, output_path, replacements)
    elif ext == ".csv":
        # This part still uses the old replacement logic - needs update
        replace_entities_in_csv(input_path, output_path, replacements)
    elif ext == ".txt":
        # --- Apply positional replacement for the TXT file ---
        # We pass the original text content, the global replacements table,
        # and the entities WITH offsets specific to the TXT block.
        if texts and texts[0].strip(): # Ensure there's a non-empty block
             # Pass the text content directly (texts[0]) as the first arg to apply_positional_replacements
             # replace_entities_in_txt now handles the file reading/writing
             replace_entities_in_txt(input_path, output_path, replacements, entities_per_block_with_offsets[0])
        else: # If the TXT file was empty, just copy the empty file
            with open(input_path, 'r', encoding='utf-8') as fin, \
                 open(output_path, 'w', encoding='utf-8') as fout:
                 fout.write(fin.read())


    typer.secho(f"✅ Anonymisation terminée: {output_path}", fg=typer.colors.GREEN)


@app.command("list-entities")
def list_entities(
    model: str = typer.Option("fr_core_news_md", "-m", "--model", help="Modèle spaCy à utiliser.")
):
    """Liste les types d'entités reconnus par le modèle spaCy."""
    import spacy
    try:
        # Use the global engine instance if it uses the correct model, otherwise load
        if engine.nlp.meta['lang'] + '_' + engine.nlp.meta['name'] == model.replace('-', '_'):
             nlp = engine.nlp
             typer.echo(f"Utilisation du modèle chargé '{model}'.")
        else:
             typer.echo(f"Chargement du modèle '{model}'.")
             nlp = spacy.load(model)

        labels = nlp.get_pipe("ner").labels
        typer.echo(f"Entités reconnues par le modèle '{model}':")
        for label in labels:
            typer.echo(f"- {label}")
        # Also mention the custom EMAIL entity if applicable
        # Assuming EMAIL is added for these models
        if model in ["fr_core_news_md", "fr_core_news_sm", "fr_dep_news_wangbert"]: # Add other models if EMAIL regex is used there
             typer.echo("- EMAIL (détecté par regex)")

    except OSError:
         typer.secho(f"Erreur : Modèle spaCy '{model}' non trouvé. Assurez-vous qu'il est installé.", fg=typer.colors.RED)
         typer.echo("Vous pouvez installer des modèles avec : python -m spacy download [model_name]")
         raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Une erreur est survenue lors du chargement ou de la liste des entités : {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()