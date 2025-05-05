# anonymizer/excel_processor.py
import pandas as pd
import os # Import os for directory creation
from .spacy_engine import SpaCyEngine
from .anonymizer_core import collect_and_anonymize_text_blocks # Import the core anonymizer function


def extract_text_from_excel(path):
    """Extrait le texte cellule par cellule depuis un fichier Excel."""
    df = pd.read_excel(path)
    cell_texts = []
    # Extract text from each cell, similar to CSV, treat each as a block
    for row_index in range(df.shape[0]):
        for col_index in range(df.shape[1]):
            cell_value = df.iloc[row_index, col_index]
            # Ensure we are treating potential non-string values as strings for analysis
            cell_texts.append(str(cell_value) if pd.notna(cell_value) else '') # Handle NaN

    return cell_texts

def replace_entities_in_excel(input_path, output_path):
    """Remplace les entités dans un fichier Excel cellule par cellule en utilisant l'anonymisation basée sur la position."""

    df = pd.read_excel(input_path)

    if df.empty:
         # If the DataFrame is empty, save an empty Excel file
         df.to_excel(output_path, index=False)
         return

    # Extract all cell contents as text blocks for entity collection
    text_blocks = []
    for row_index in range(df.shape[0]):
        for col_index in range(df.shape[1]):
            cell_value = df.iloc[row_index, col_index]
            text_blocks.append(str(cell_value) if pd.notna(cell_value) else '') # Handle NaN

    # Use the core function to collect entities and anonymize the text blocks (cells)
    spacy_engine = SpaCyEngine() # Instantiate SpaCyEngine
    anonymized_text_blocks = collect_and_anonymize_text_blocks(text_blocks, spacy_engine)

    # Create a new DataFrame or modify the existing one with anonymized content
    anonymized_df = df.copy() # Create a copy to modify

    block_index = 0
    for row_index in range(anonymized_df.shape[0]):
        for col_index in range(anonymized_df.shape[1]):
            # Get the corresponding anonymized block (cell content)
            anonymized_cell = anonymized_text_blocks[block_index]
            anonymized_df.iloc[row_index, col_index] = anonymized_cell
            block_index += 1

    # Ensure output directory exists (already in original code, kept for robustness)
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Save the modified DataFrame
    anonymized_df.to_excel(output_path, index=False)