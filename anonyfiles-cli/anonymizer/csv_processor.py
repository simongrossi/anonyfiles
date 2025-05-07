import csv
import os

def extract_text_from_csv(path):
    """Extrait le texte cellule par cellule depuis un fichier CSV."""
    cell_texts = []
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            cell_texts.extend(row)
    return cell_texts

def replace_entities_in_csv(input_path, output_path, replacements):
    """Remplace les entités dans un fichier CSV cellule par cellule en utilisant les remplacements fournis."""
    original_rows = []
    with open(input_path, mode='r', encoding='utf-8') as fin:
        reader = csv.reader(fin)
        for row in reader:
            original_rows.append(row)

    if not original_rows:
        with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
            pass
        return

    anonymized_rows = []
    for row in original_rows:
        new_row = []
        for cell in row:
            cell_text = str(cell)
            for entity_text, replacement in replacements.items():
                if entity_text in cell_text:
                    cell_text = cell_text.replace(entity_text, replacement)
            new_row.append(cell_text)
        anonymized_rows.append(new_row)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
        writer = csv.writer(fout)
        writer.writerows(anonymized_rows)
