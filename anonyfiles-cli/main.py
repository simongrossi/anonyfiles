# main.py
import typer
import os
import csv
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any # Import Dict and Any for configuration typing
import importlib.metadata
import re

# Import PyYAML for configuration file reading
import yaml
from yaml import YAMLError

# Import the modified processor files
from anonymizer.spacy_engine import SpaCyEngine, EMAIL_REGEX
from anonymizer.word_processor import extract_text_from_docx, replace_entities_in_docx
from anonymizer.excel_processor import extract_text_from_excel, replace_entities_in_excel
from anonymizer.txt_processor import extract_text_from_txt, replace_entities_in_txt
from anonymizer.csv_processor import extract_text_from_csv, replace_entities_in_csv
# Import generate_replacements from the modified replacer.py
from anonymizer.replacer import generate_replacements

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
# This loads the default model (fr_core_news_md) - Model can be overridden by config/CLI
engine = SpaCyEngine()

# Define default configuration structure
DEFAULT_CONFIG: Dict[str, Any] = {
    "spacy_model": "fr_core_news_md",
    "entities_to_anonymize": [], # Empty list means all detected entities
    "output_dir": "output_files",
    "replacements": {
        # Default fallbacks - these will be used if not specified in the config file
        # The replacer.py will need to handle these rules
        "PER": {"type": "codes", "options": {"prefix": "NOM", "padding": 3}},
        "LOC": {"type": "faker"},
        "ORG": {"type": "redact"},
        "DATE": {"type": "faker"},
        "EMAIL": {"type": "faker"},
        "MISC": {"type": "redact"},
        # Add other default types/rules here
    },
    "log": {
        "path": "log/entities.csv"
    },
    # Placeholder for other potential config settings
}


def load_config(config_path: Optional[Path]) -> Dict[str, Any]:
    """Loads configuration from a YAML file, merging with defaults."""
    config = DEFAULT_CONFIG.copy() # Start with a copy of defaults

    if config_path:
        if not config_path.exists():
            typer.secho(f"Erreur : Fichier de configuration non trouvé : {config_path}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # Simple merge - user config overrides defaults
                    # For nested dicts like 'replacements', a deeper merge might be needed
                    # but for this simple structure, a top-level update is OK for now.
                    config.update(user_config)
            typer.echo(f"⚙️ Configuration chargée depuis : {config_path}")
        except YAMLError as e:
            typer.secho(f"Erreur lors de la lecture du fichier de configuration {config_path}: {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
        except Exception as e:
             typer.secho(f"Une erreur inattendue est survenue lors du chargement de la configuration {config_path}: {e}", fg=typer.colors.RED)
             raise typer.Exit(code=1)

    # Basic validation for replacements structure
    if 'replacements' not in config or not isinstance(config['replacements'], dict):
         typer.secho("Avertissement : La section 'replacements' est absente ou invalide dans la configuration. Utilisation des règles par défaut.", fg=typer.colors.YELLOW)
         config['replacements'] = DEFAULT_CONFIG['replacements'] # Fallback to default replacements

    return config


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
    output_filename: Optional[Path] = typer.Option(None, "-o", "--output", help="Chemin de sortie (par défaut output_files/...)"),
    # Removed --entities option as it's now primarily in config
    # entities: List[str] = typer.Option([], "-e", "--entities", help="Types d'entités à anonymiser (ex: PER LOC ORG DATE EMAIL). Toutes si vide."),
    log_entities: Optional[Path] = typer.Option(None, "-l", "--log-entities", help="Exporter les entités détectées vers un fichier CSV."),
    mapping_output: Optional[Path] = typer.Option(None, "--mapping-output", help="Exporter la table de correspondance Nom original -> Code (pour les entités PER) vers un fichier CSV."),
    # Removed --fake-data / --redact options as replacement types are now in config
    # fake_data: bool = typer.Option(True, "--fake-data/--redact", help="Mode de remplacement : Faker (par défaut) ou [REDACTED]."),
    dry_run: bool = typer.Option(False, "-n", "--dry-run", help="Simule sans écrire de fichier."),
    verbose: bool = typer.Option(False, "--verbose", help="Mode verbeux (debug)."),
    # Add config file option
    config_path: Optional[Path] = typer.Option(None, "--config", "-c", help="Chemin vers le fichier de configuration YAML."),
):
    """Anonymise le fichier spécifié selon la configuration ou les options CLI."""
    setup_logging(verbose)

    # --- Load Configuration ---
    config = load_config(config_path)
    typer.echo(f"Configuration effective : {config}") # Log effective config


    # --- Apply CLI overrides to config ---
    # CLI options take precedence over config file
    if log_entities is None and config.get("log", {}).get("path"):
        # Use log path from config if not specified in CLI
        log_entities = Path(config["log"]["path"])
    elif log_entities is not None and config.get("log", {}).get("path"):
        # CLI option overrides config, but make sure parent dir exists if config path was used as base
        log_entities.parent.mkdir(parents=True, exist_ok=True)
        pass # Use CLI path

    # Determine effective output directory
    output_dir = Path(config.get("output_dir", DEFAULT_CONFIG["output_dir"]))

    # --- Construct paths ---
    input_path = Path("input_files") / input_filename
    ext = input_filename.suffix.lower()
    # Calculate output path based on option or default
    output_path = output_filename or (output_dir / f"{input_filename.stem}_anonymise{ext}")

    typer.echo(f"🔍 Lecture de : {input_path}")
    # Now perform the existence check after constructing the correct path
    if not input_path.exists():
        typer.secho(f"Erreur : fichier non trouvé {input_path}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    # --- Ensure output directory exists early if not dry run ---
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        # Ensure output_path parent directory exists if output_filename was explicitly set outside default output_dir
        output_path.parent.mkdir(parents=True, exist_ok=True)


    # --- Extraction du texte et détection des entités avec et sans offsets ---
    texts: List[str] = []
    all_entities_for_replacement_generation = []
    entities_per_block_with_offsets = []
    original_file_data = None

    # Use model from config, falling back to default if not specified
    model_name = config.get("spacy_model", DEFAULT_CONFIG["spacy_model"])
    # Check if the global engine is using the correct model, if not, re-initialize
    # Note: This simple check might be insufficient if different configs use different models.
    # A more robust solution might pass the model name to detect_entities or re-initialize engine here.
    # For now, assume the global engine is sufficient or will be re-initialized if model differs.
    # print(f"Engine model: {engine.nlp.meta['lang']}_{engine.nlp.meta['name']}, Config model: {model_name.replace('-', '_')}") # Debugging model check
    if engine.nlp.meta['lang'] + '_' + engine.nlp.meta['name'] != model_name.replace('-', '_'):
        typer.echo(f"Chargement du modèle spaCy : {model_name}")
        try:
            engine = SpaCyEngine(model=model_name)
        except OSError:
             typer.secho(f"Erreur : Modèle spaCy '{model_name}' non trouvé. Assurez-vous qu'il est installé.", fg=typer.colors.RED)
             typer.echo("Vous pouvez installer des modèles avec : python -m spacy download [model_name]")
             raise typer.Exit(code=1)
        except Exception as e:
             typer.secho(f"Une erreur est survenue lors du chargement du modèle spaCy '{model_name}' : {e}", fg=typer.colors.RED)
             raise typer.Exit(code=1)


    if ext == ".docx":
        typer.echo("Traitement Word (.docx)")
        paragraph_texts = extract_text_from_docx(input_path)
        texts = paragraph_texts

        for p_text in paragraph_texts:
            if p_text.strip():
                 doc = engine.nlp(p_text)
                 block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
                 entities_per_block_with_offsets.append(block_entities_with_offsets)
                 all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
                 email_matches = re.findall(EMAIL_REGEX, p_text)
                 all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])
            else:
                 entities_per_block_with_offsets.append([])


    elif ext == ".xlsx":
        typer.echo("Traitement Excel (.xlsx)")
        try:
            df = pd.read_excel(input_path)
            original_file_data = df
        except Exception as e:
            typer.secho(f"Erreur lors de la lecture du fichier Excel : {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        cell_values = df.values.flatten()
        texts = [str(value) if pd.notna(value) else '' for value in cell_values]

        for cell_text in texts:
             if cell_text.strip():
                  doc = engine.nlp(cell_text)
                  block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
                  entities_per_block_with_offsets.append(block_entities_with_offsets)
                  all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
                  email_matches = re.findall(EMAIL_REGEX, cell_text)
                  all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])
             else:
                  entities_per_block_with_offsets.append([])


    elif ext == ".csv":
        typer.echo("Traitement CSV (.csv)")
        csv_data = []
        try:
            with open(input_path, mode='r', encoding='utf-8') as fin:
                reader = csv.reader(fin)
                for row in reader:
                    original_row = [str(cell) for cell in row]
                    csv_data.append(original_row)
            original_file_data = csv_data
        except Exception as e:
            typer.secho(f"Erreur lors de la lecture du fichier CSV : {e}", fg=typer.colors.RED)
            raise typer.Exit(code=1)

        for row_index, row in enumerate(csv_data):
            for col_index, cell_text in enumerate(row):
                texts.append(cell_text)

                if cell_text.strip():
                    doc = engine.nlp(cell_text)
                    block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
                    entities_per_block_with_offsets.append(block_entities_with_offsets)
                    all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
                    email_matches = re.findall(EMAIL_REGEX, cell_text)
                    all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])
                else:
                    entities_per_block_with_offsets.append([])


    elif ext == ".txt":
        typer.echo("Traitement TXT (.txt)")
        text_content = extract_text_from_txt(input_path)
        texts = [text_content]

        if text_content.strip():
             doc = engine.nlp(text_content)
             block_entities_with_offsets = [(ent.text, ent.label_, ent.start_char, ent.end_char) for ent in doc.ents]
             entities_per_block_with_offsets.append(block_entities_with_offsets)
             all_entities_for_replacement_generation.extend([(ent.text, ent.label_) for ent in doc.ents])
             email_matches = re.findall(EMAIL_REGEX, text_content)
             all_entities_for_replacement_generation.extend([(email, "EMAIL") for email in email_matches])
        else:
             entities_per_block_with_offsets.append([])


    else:
        typer.secho(f"Type de fichier non supporté : {ext}", fg=typer.colors.RED)
        raise typer.Exit(code=1)


    # --- Filtering global entities based on config/CLI ---
    unique_entities = list(set(all_entities_for_replacement_generation))

    # Filter based on entities_to_anonymize from config
    entities_filter = config.get("entities_to_anonymize", DEFAULT_CONFIG["entities_to_anonymize"])
    if entities_filter:
        selected = set(entities_filter)
        unique_entities = [(t, l) for t, l in unique_entities if l in selected]
        typer.echo(f"Entités filtrées (selon config) : {selected}")
    # Note: If a --entities CLI option is re-added later, it should override config['entities_to_anonymize']


    if not unique_entities:
        typer.echo("Aucune entité détectée selon les critères spécifiés.")
        # Create an empty output file if input was empty or no entities found and not dry run
        if not dry_run:
             if ext == ".docx": Document().save(output_path)
             elif ext == ".xlsx": pd.DataFrame().to_excel(output_path, index=False)
             elif ext == ".csv": Path(output_path).write_text("")
             elif ext == ".txt": Path(output_path).write_text("")
        return


    # --- Generate *global* replacements AND the person code map ---
    # Pass the replacements config to generate_replacements
    # The function will now use these rules and also return the person_code_map
    replacements, person_code_map = generate_replacements(
        unique_entities,
        replacement_rules=config.get("replacements", DEFAULT_CONFIG["replacements"]) # Pass rules from config
        )

    typer.echo(f"Entités uniques détectées ({len(unique_entities)}): {unique_entities[:10]}...")
    typer.echo(f"Règles de remplacement appliquées (extrait) : {dict(list(config.get('replacements',{}).items())[:5])}...") # Log applied rules
    typer.echo(f"Remplacements générés (extrait): {dict(list(replacements.items())[:5])}...")


    # --- Export detected entities log ---
    if log_entities and unique_entities:
         log_path = log_entities # log_entities is already a Path object from CLI or config
         log_path.parent.mkdir(parents=True, exist_ok=True)
         try:
            with open(log_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Entite", "Label"])
                for t, l in unique_entities:
                    writer.writerow([t, l])
            typer.secho(f"✅ Entités uniques détectées exportées vers {log_path}", fg=typer.colors.GREEN)
         except Exception as e:
             typer.secho(f"⚠️ Erreur lors de l'export du log des entités : {e}", fg=typer.colors.YELLOW)


    # --- Export Person Code Mapping (New Logic) ---
    if person_code_map:
        # Determine mapping file path: default to same dir as output file, with _mapping suffix
        mapping_file_path = mapping_output or (output_path.parent / f"{output_path.stem}_mapping.csv")

        try:
            mapping_file_path.parent.mkdir(parents=True, exist_ok=True)
            typer.echo(f"✍️ Export de la table de correspondance Nom original -> Code vers : {mapping_file_path}")

            with open(mapping_file_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Code", "Nom Original"])
                inverted_person_code_map = {code: name for name, code in person_code_map.items()}
                for code in sorted(inverted_person_code_map.keys()):
                     original_name = inverted_person_code_map[code]
                     writer.writerow([code, original_name])

            typer.secho(f"✅ Table de correspondance Nom original -> Code exportée.", fg=typer.colors.GREEN)

        except Exception as e:
            typer.secho(f"⚠️ Erreur lors de l'export de la table de correspondance : {e}", fg=typer.colors.YELLOW)


    if dry_run:
        typer.echo("--dry-run: aucun fichier de sortie généré.")
        return


    # --- Application des remplacements ---
    # Output directory is already ensured to exist if not dry_run
    typer.echo(f"💾 Écriture de : {output_path}")

    if ext == ".docx":
        typer.echo("Application remplacement positionnel Word (.docx)")
        if texts:
             replace_entities_in_docx(input_path, output_path, replacements, entities_per_block_with_offsets)
        else:
             Document().save(output_path)


    elif ext == ".xlsx":
        typer.echo("Application remplacement positionnel Excel (.xlsx)")
        if original_file_data is not None:
             replace_entities_in_excel(input_path, output_path, replacements, original_file_data, entities_per_block_with_offsets)
        else:
             pd.DataFrame().to_excel(output_path, index=False)


    elif ext == ".csv":
         typer.echo("Application remplacement positionnel CSV (.csv)")
         if original_file_data is not None:
              replace_entities_in_csv(input_path, output_path, replacements, original_file_data, entities_per_block_with_offsets)
         else:
             Path(output_path).write_text("")


    elif ext == ".txt":
        typer.echo("Application remplacement positionnel TXT (.txt)")
        if texts and texts[0].strip():
             replace_entities_in_txt(input_path, output_path, replacements, entities_per_block_with_offsets[0])
        else:
            Path(output_path).write_text("")


    typer.secho(f"✅ Anonymisation terminée: {output_path}", fg=typer.colors.GREEN)


@app.command("list-entities")
def list_entities(
    # Use model from default config, not hardcoded "fr_core_news_md"
    model: str = typer.Option(DEFAULT_CONFIG["spacy_model"], "-m", "--model", help="Modèle spaCy à utiliser.")
):
    """Liste les types d'entités reconnus par le modèle spaCy."""
    import spacy
    try:
        # Try using the global engine first if model matches, otherwise load
        # This check is simplified here compared to the one in anonymize command
        # For robustness, loading here might be better if model option is used
        nlp = engine.nlp # Assume engine is initialized with a default model
        if nlp.meta['lang'] + '_' + nlp.meta['name'] != model.replace('-', '_'):
             typer.echo(f"Chargement du modèle '{model}' pour la liste des entités...")
             nlp = spacy.load(model)
        else:
            typer.echo(f"Utilisation du modèle chargé '{nlp.meta['lang']}_{nlp.meta['name']}'.")


        labels = nlp.get_pipe("ner").labels
        typer.echo(f"Entités reconnues par le modèle '{model}':")
        for label in labels:
            typer.echo(f"- {label}")
        # Also mention the custom EMAIL entity if applicable
        # This list should ideally be driven by which models the regex was tested with
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