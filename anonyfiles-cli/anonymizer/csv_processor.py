# anonymizer/csv_processor.py
import csv
from .spacy_engine import SpaCyEngine
from .anonymizer_core import collect_and_anonymize_text_blocks # Import the core anonymizer function

def extract_text_from_csv(path):
    """Extrait le texte cellule par cellule depuis un fichier CSV."""
    cell_texts = []
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Treat each cell as a separate text block
            cell_texts.extend(row)
    # Note: This extracts all cell texts into a single list for entity collection.
    # The structure (rows/cols) is lost here but rebuilt during writing.
    return cell_texts

def replace_entities_in_csv(input_path, output_path):
    """Remplace les entités dans un fichier CSV cellule par cellule en utilisant l'anonymisation basée sur la position."""

    # Read the original CSV content to reconstruct it later
    original_rows = []
    with open(input_path, mode='r', encoding='utf-8') as fin:
        reader = csv.reader(fin)
        for row in reader:
            original_rows.append(row)

    if not original_rows:
        # If the file is empty, just create an empty output file
        with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
             pass # Create an empty file
        return

    # Extract text from each cell to pass as blocks to the core anonymizer
    text_blocks = []
    for row in original_rows:
        for cell in row:
            # Treat each cell content as a text block
            text_blocks.append(cell if isinstance(cell, str) else str(cell)) # Ensure it's a string

    # Use the core function to collect entities and anonymize the text blocks (cells)
    spacy_engine = SpaCyEngine() # Instantiate SpaCyEngine
    anonymized_text_blocks = collect_and_anonymize_text_blocks(text_blocks, spacy_engine)

    # Reconstruct the CSV rows with anonymized cell content
    anonymized_rows = []
    block_index = 0
    for row in original_rows:
        new_row = []
        for cell in row:
            # Get the corresponding anonymized block (cell content)
            anonymized_cell = anonymized_text_blocks[block_index]
            new_row.append(anonymized_cell)
            block_index += 1
        anonymized_rows.append(new_row)


    # Write the anonymized content to the output file
    with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
        writer = csv.writer(fout)
        writer.writerows(anonymized_rows)