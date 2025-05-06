# anonymizer/txt_processor.py
from .spacy_engine import SpaCyEngine
from .anonymizer_core import collect_and_anonymize_text_blocks # Import the core anonymizer function

def extract_text_from_txt(path):
    """Extrait le texte complet d'un fichier .txt."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read() # Read the entire file as a single block

def replace_entities_in_txt(input_path, output_path):
    """Remplace les entités dans un fichier texte en utilisant l'anonymisation basée sur la position."""
    text_content = extract_text_from_txt(input_path)

    if not text_content.strip():
        # If the file is empty or only contains whitespace, just copy it
        with open(input_path, 'r', encoding='utf-8') as fin, \
             open(output_path, 'w', encoding='utf-8') as fout:
            fout.write(text_content)
        return

    # Use the core function to collect entities and anonymize the single text block
    # Pass the text content as a list containing one block
    spacy_engine = SpaCyEngine() # Instantiate SpaCyEngine
    anonymized_blocks = collect_and_anonymize_text_blocks([text_content], spacy_engine)

    # anonymized_blocks will contain one element: the anonymized text content
    anonymized_text_content = anonymized_blocks[0]

    with open(output_path, 'w', encoding='utf-8') as fout:
        fout.write(anonymized_text_content)