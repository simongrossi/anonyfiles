# main.py
import typer
import os
import csv # Importer le module csv pour l'export du mapping
import logging
from pathlib import Path
from typing import List, Optional
import importlib.metadata
import re # Import the 're' module

# Import the modified processor files
from anonymizer.spacy_engine import SpaCyEngine, EMAIL_REGEX # Import SpaCyEngine and EMAIL_REGEX
from anonymizer.word_processor import extract_text_from_docx, replace_entities_in_docx
from anonymizer.excel_processor import extract_text_from_excel, replace_entities_in_excel
from anonymizer.txt_processor import extract_text_from_txt, replace_entities_in_txt
from anonymizer.csv_processor import extract_text_from_csv, replace_entities_in_csv
# Import generate_replacements from the modified replacer.py
from anonymizer.replacer import generate_replacements # IMPORTANT: This function now returns two values!

# Needed for creating empty docx file
from docx import Document

# Needed for reading xlsx file
import pandas as pd


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
    input_filename: Path = typer.Argument(..., file_okay=True, readable=True, help="Fichier à anonymiser (dans input_files/)"),
    output_filename: Optional[Path] = typer.Option(None, "-o", "--output", help="Chemin de sortie (par défaut output_files/)"),
    entities: List[str] = typer.Option([], "-e", "--entities", help="Types d'entités à anonymiser (ex: PER LOC ORG DATE EMAIL). Toutes si vide."),
    log_entities: Optional[Path] = typer.Option(None, "-l", "--log-entities", help="Exporter les entités détectées vers un fichier CSV."),
    # Nouvelle option pour le fichier de mapping des codes personne
    mapping_output: Optional[Path] = typer.Option(None, "--mapping-output", help="Exporter la table de correspondance Nom original -> Code (pour les entités PER) vers un fichier CSV."),
    dry_run: bool = typer.Option(False, "-n", "--dry-run", help="Simule sans écrire de fichier."),
    verbose: bool = typer.Option(False, "--verbose", help="Mode verbeux (debug).")
):
    """Anonymise le fichier spécifié."""
    setup_logging(verbose)

    # Construct the full input path
    input_path = Path("input_files") / input_filename

    # Extract the file extension and convert to lowercase
    ext = input_filename.suffix.lower()

    # Calculate output path based on option or default BEFORE checks that might return
    output_path = output_filename or (Path("output_files") / f"{input_filename.stem}_anonymise{ext}")

    typer.echo(f"🔍 Lecture de : {input_path}")
    # Now perform the existence check after constructing the correct path
    if not input_path.exists():
        typer.secho(f"Erreur : fichier non trouvé {input_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # --- Extraction du texte et détection des entités avec et sans offsets ---
    texts: List[str] = [] # Liste plate de tous les textes extraits (pour détection globale)
    all_entities_for_replacement_generation = [] # For global replacement generation (text, label)
    entities_per_block_with_offsets = [] # For positional replacement (text, label, start, end) - each entry is a list for a block (cell, paragraph, etc.)

    # --- Variables pour stocker les données structurées par type de fichier ---
    original_file_data = None # Pour CSV (liste de listes) ou XLSX (DataFrame)


    if ext == ".docx":
        typer.echo("Traitement Word (.docx)")
        paragraph_texts = extract_text_from_docx(input_path)
        texts = paragraph_texts # Conserver la liste des textes de paragraphe

        # --- Detect entities *with offsets* for EACH paragraph (block) ---
        for p_text in paragraph_texts:
            if p_text.strip():
                 doc = engine.nlp(p_text)
                 block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
                 entities_per_block_with_offsets.append(block_entities_with_offsets)

                 # --- Also collect entities (without offsets) for global replacement generation ---
                 all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
                 email_matches = re.findall(EMAIL_REGEX, p_text)
                 all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])
            else:
                 entities_per_block_with_offsets.append([]) # Empty paragraph


    elif ext == ".xlsx":
        typer.echo("Traitement Excel (.xlsx)")
        # --- Read Excel data into a pandas DataFrame ---
        try:
            df = pd.read_excel(input_path)
            original_file_data = df # Store the DataFrame
        except Exception as e:
            typer.secho(f"Erreur lors de la lecture du fichier Excel : {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        # --- Iterate through DataFrame cells for detection with offsets and global entity collection ---
        # Flatten the DataFrame values to iterate through cell texts
        cell_values = df.values.flatten()
        # texts will be the list of string representations of cell values for global detection
        texts = [str(value) if pd.notna(value) else '' for value in cell_values]

        # Iterate through the flat list of cell texts for detection with offsets
        for cell_text in texts: # This loop iterates over flattened texts from the DataFrame
             if cell_text.strip():
                  doc = engine.nlp(cell_text)
                  # Store entities with offsets for this cell (block)
                  block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
                  entities_per_block_with_offsets.append(block_entities_with_offsets)

                  # --- Also collect entities (without offsets) for global replacement generation ---
                  all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
                  email_matches = re.findall(EMAIL_REGEX, cell_text)
                  all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])
             else:
                  entities_per_block_with_offsets.append([]) # Empty cell


    elif ext == ".csv":
        typer.echo("Traitement CSV (.csv)")
        # --- Read CSV data into a list of lists ---
        csv_data = []
        try:
            with open(input_path, mode='r', encoding='utf-8') as fin:
                reader = csv.reader(fin)
                for row in reader:
                    original_row = [str(cell) for cell in row] # Ensure cells are strings
                    csv_data.append(original_row)
            original_file_data = csv_data # Store the list of lists
        except Exception as e:
            typer.secho(f"Erreur lors de la lecture du fichier CSV : {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)


        # --- Collect cell texts for global detection and detect entities with offsets for EACH cell (block) ---
        # Iterate through rows and cells of the structured data
        for row_index, row in enumerate(csv_data):
            for col_index, cell_text in enumerate(row):
                texts.append(cell_text) # Add cell text to the flat list for global detection

                if cell_text.strip():
                    doc = engine.nlp(cell_text)
                    # Store entities with offsets for this cell (block)
                    block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
                    entities_per_block_with_offsets.append(block_entities_with_offsets)

                    # --- Also collect entities (without offsets) for global replacement generation ---
                    all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
                    email_matches = re.findall(EMAIL_REGEX, cell_text)
                    all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])
                else:
                    entities_per_block_with_offsets.append([]) # Empty cell


    elif ext == ".txt":
        typer.echo("Traitement TXT (.txt)")
        text_content = extract_text_from_txt(input_path)
        texts = [text_content] # Store the text in a list (single block)

        # --- Detect entities *with offsets* for the TXT block ---
        if text_content.strip():
             doc = engine.nlp(text_content)
             # Store entities with offsets for positional replacement (for the single TXT block)
             block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
             entities_per_block_with_offsets.append(block_entities_with_offsets) # Append as a list for consistency

             # --- Also collect entities (without offsets) for global replacement generation ---
             all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
             email_matches = re.findall(EMAIL_REGEX, text_content)
             all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])

        else:
             entities_per_block_with_offsets.append([]) # Empty block


    else: # Type de fichier non supporté (should be caught earlier, but good practice)
        typer.secho(f"Type de fichier non supporté : {ext}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


    # --- Filtering global entities based on selected types ---
    # Create a set of unique entities (text, label) regardless of their location
    unique_entities = list(set(all_entities_for_replacement_generation))

    if entities:
        selected = set(entities)
        # Filter the global list of entities before generating replacements
        unique_entities = [(t, l) for t, l in unique_entities if l in selected]
        typer.echo(f"Entités filtrées : {selected}")


    if not unique_entities: # Check unique_entities as it's the base for replacements
        typer.echo("Aucune entité détectée selon les critères spécifiés.")
        # If no entities detected, the output file should ideally be a copy of the input
        # However, the current flow exits here, preventing output writing.
        # This might be acceptable if no anonymization is needed.
        return # Exit the command if no entities found


    # --- Generate *global* replacements AND the person code map ---
    # Capture both return values from the modified generate_replacements
    # replacements is the {original_text: replacement_text} map for all entity types processed
    # person_code_map is the {original_name: code} map specifically for PER entities
    replacements, person_code_map = generate_replacements(unique_entities)

    typer.echo(f"Entités uniques détectées ({len(unique_entities)}): {unique_entities[:10]}...") # Show only a sample
    typer.echo(f"Remplacements générés (extrait): {dict(list(replacements.items())[:5])}...") # Show only a sample


    # --- Export detected entities log (existing logic) ---
    if log_entities and unique_entities: # Use unique_entities for log as it's the base for replacements
         log_path = Path("log") / log_entities
         log_path.parent.mkdir(parents=True, exist_ok=True)
         try:
            with open(log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Entite", "Label"])
                # Log the unique entities that were detected/filtered
                for t, l in unique_entities:
                    writer.writerow([t, l])
            typer.echo(f"✅ Entités exportées vers {log_path}")
         except Exception as e:
             typer.secho(f"⚠️ Erreur lors de l'export du log des entités : {e}", fg=typer.colors.YELLOW) # Changed to Warning


    # --- Export Person Code Mapping (New Logic) ---
    # Only save if there were person entities found and coded (person_code_map won't be empty if PER entities were processed)
    if person_code_map:
        # Determine mapping file path: default to same dir as output file, with _mapping suffix
        mapping_file_path = mapping_output or (output_path.parent / f"{output_path.stem}_mapping.csv")

        try:
            # Ensure the directory exists
            mapping_file_path.parent.mkdir(parents=True, exist_ok=True)

            typer.echo(f"✍️ Export de la table de correspondance NOM->Code vers : {mapping_file_path}")

            with open(mapping_file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Write header: Code, Original Name
                writer.writerow(["Code", "Nom Original"])
                # Write mapping rows: iterate through the person_code_map
                # person_code_map is {Original Name: Code}, need {Code: Original Name} for reversal
                # Invert the map for saving
                inverted_person_code_map = {code: name for name, code in person_code_map.items()}
                # Sort by code (NOM001, NOM002...) for readability in the mapping file
                for code in sorted(inverted_person_code_map.keys()):
                     original_name = inverted_person_code_map[code]
                     writer.writerow([code, original_name])

            typer.secho(f"✅ Table de correspondance Nom original -> Code exportée.", fg=typer.colors.GREEN)

        except Exception as e:
            typer.secho(f"⚠️ Erreur lors de l'export de la table de correspondance : {e}", fg=typer.colors.YELLOW) # Changed to Warning


    if dry_run:
        typer.echo("--dry-run: aucun fichier de sortie généré.")
        return


    # --- Application des remplacements ---
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    typer.echo(f"💾 Écriture de : {output_path}")

    if ext == ".docx":
        typer.echo("Application remplacement positionnel Word (.docx)")
        if texts: # Ensure there are paragraphs (texts was populated with paragraph_texts)
             # entities_per_block_with_offsets is a list of lists, one list per paragraph
             replace_entities_in_docx(input_path, output_path, replacements, entities_per_block_with_offsets)
        else: # If the DOCX file was empty, create an empty docx
             Document().save(output_path)


    elif ext == ".xlsx":
        typer.echo("Application remplacement positionnel Excel (.xlsx)")
        # --- Apply positional replacement for the XLSX file ---
        # Call the modified replace_entities_in_excel function
        if original_file_data is not None: # Ensure DataFrame was populated and stored in original_file_data
             # entities_per_block_with_offsets contains entities with offsets per cell
             replace_entities_in_excel(input_path, output_path, replacements, original_file_data, entities_per_block_with_offsets)
        else: # If the XLSX file was empty, create an empty excel
             pd.DataFrame().to_excel(output_path, index=False)


    elif ext == ".csv":
         typer.echo("Application remplacement positionnel CSV (.csv)")
         # --- Apply positional replacement for the CSV file ---
         if original_file_data is not None: # Ensure csv_data was populated and stored in original_file_data
              # Pass original_file_data (list of lists) and entities_per_block_with_offsets (entities with offsets per cell)
              replace_entities_in_csv(input_path, output_path, replacements, original_file_data, entities_per_block_with_offsets)
         else: # If the CSV file was empty, create an empty csv
             with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                 pass


    elif ext == ".txt":
        typer.echo("Application remplacement positionnel TXT (.txt)")
        # Apply positional replacement for the TXT file (already implemented)
        # texts list has only one item for TXT files (the whole content)
        if texts and texts[0].strip(): # Ensure there's a non-empty block
             # entities_per_block_with_offsets is a list containing one list of entities for the TXT block
             replace_entities_in_txt(input_path, output_path, replacements, entities_per_block_with_offsets[0])
        else: # If the TXT file was empty, just copy the empty file content (which is empty)
            # This ensures an empty output file is created if the input is empty
            output_path.write_text("")


    # Removed redundant else block for unhandled file types as it's checked earlier


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
        if model in ["fr_core_news_md", "fr_core_news_sm"]: # Add other models if EMAIL regex is used there
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