import pandas as pd
import os

def extract_text_from_excel(path):
    """Extrait le texte cellule par cellule depuis un fichier Excel."""
    df = pd.read_excel(path)
    cell_texts = []
    for row_index in range(df.shape[0]):
        for col_index in range(df.shape[1]):
            cell_value = df.iloc[row_index, col_index]
            cell_texts.append(str(cell_value) if pd.notna(cell_value) else '')
    return cell_texts

def replace_entities_in_excel(input_path, output_path, replacements):
    """Remplace les entités dans un fichier Excel à l'aide de la table de remplacement."""
    df = pd.read_excel(input_path)

    if df.empty:
        df.to_excel(output_path, index=False)
        return

    anonymized_df = df.copy()

    for row_index in range(anonymized_df.shape[0]):
        for col_index in range(anonymized_df.shape[1]):
            cell_value = anonymized_df.iloc[row_index, col_index]
            if pd.isna(cell_value):
                continue

            cell_text = str(cell_value)
            for entity_text, replacement in replacements.items():
                if entity_text in cell_text:
                    cell_text = cell_text.replace(entity_text, replacement)

            anonymized_df.iloc[row_index, col_index] = cell_text

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    anonymized_df.to_excel(output_path, index=False)
