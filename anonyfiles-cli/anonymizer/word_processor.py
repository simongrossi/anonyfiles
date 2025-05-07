from docx import Document
import os

def extract_text_from_docx(path):
    """Extrait le texte d'un fichier .docx, paragraphe par paragraphe."""
    doc = Document(path)
    return [p.text for p in doc.paragraphs]

def replace_entities_in_docx(path, output_path, replacements):
    """Remplace les entités dans un fichier .docx à l’aide de la table de remplacements."""
    doc = Document(path)
    paragraphs = doc.paragraphs

    if not paragraphs or all(not p.text.strip() for p in paragraphs):
        doc.save(output_path)
        return

    for p in paragraphs:
        original_text = p.text
        modified_text = original_text

        for entity_text, replacement in replacements.items():
            if entity_text in modified_text:
                modified_text = modified_text.replace(entity_text, replacement)

        # Nettoyer les runs
        for run_element in p._element.xpath('./w:r'):
            run_element.getparent().remove(run_element)

        if modified_text.strip():
            p.add_run(modified_text)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    doc.save(output_path)
