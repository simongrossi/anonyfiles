import csv

def extract_text_from_csv(path):
    """Extrait le texte ligne par ligne depuis un fichier CSV (chaîne jointe pour spaCy)."""
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        return [' '.join(row) for row in reader]

def replace_entities_in_csv(input_path, replacements, output_path):
    """Remplace les entités dans un fichier CSV ligne par ligne."""
    with open(input_path, mode='r', encoding='utf-8') as fin, \
         open(output_path, mode='w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)
        for row in reader:
            new_row = []
            for cell in row:
                for original, replacement in replacements.items():
                    if original.strip() in cell:
                        cell = cell.replace(original.strip(), replacement)
                new_row.append(cell)
            writer.writerow(new_row)
