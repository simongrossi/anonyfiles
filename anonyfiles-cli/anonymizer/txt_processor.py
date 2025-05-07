import os

def extract_text_from_txt(path):
    """Extrait le texte complet d'un fichier .txt."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def replace_entities_in_txt(input_path, output_path, replacements):
    """Remplace les entités dans un fichier texte avec la table de remplacements."""
    text_content = extract_text_from_txt(input_path)

    if not text_content.strip():
        with open(input_path, 'r', encoding='utf-8') as fin, \
             open(output_path, 'w', encoding='utf-8') as fout:
            fout.write(text_content)
        return

    for entity_text, replacement in replacements.items():
        if entity_text in text_content:
            text_content = text_content.replace(entity_text, replacement)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as fout:
        fout.write(text_content)
