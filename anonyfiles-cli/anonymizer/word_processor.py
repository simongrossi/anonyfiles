# anonyfiles-main/anonymizer/word_processor.py
from docx import Document
import os
from .spacy_engine import SpaCyEngine
from .anonymizer_core import collect_and_anonymize_text_blocks # Import the core anonymizer function


def extract_text_from_docx(path):
    """
    Extrait le texte d'un fichier .docx, paragraphe par paragraphe.
    Retourne une liste de textes de paragraphes.
    """
    doc = Document(path)
    return [p.text for p in doc.paragraphs] # Return list of paragraph texts

def replace_entities_in_docx(path, output_path):
    """
    Remplace les entités détectées dans un fichier .docx en utilisant
    l'anonymisation basée sur la position sur chaque paragraphe.
    ATTENTION : Cette méthode va toujours supprimer toute la mise en forme originale
    à l'intérieur des paragraphes modifiés, car elle remplace le contenu du paragraphe.
    """
    doc = Document(path)
    paragraphs = doc.paragraphs
    paragraph_texts = [p.text for p in paragraphs]

    if not any(paragraph_texts): # Check if all paragraphs are empty
         # If the document is empty, just save an empty document
         doc.save(output_path)
         return

    # Use the core function to collect entities and anonymize the paragraph text blocks
    spacy_engine = SpaCyEngine() # Instantiate SpaCyEngine
    anonymized_paragraph_texts = collect_and_anonymize_text_blocks(paragraph_texts, spacy_engine)

    # Update the document with the anonymized paragraph texts
    for i, p in enumerate(paragraphs):
        anonymized_text = anonymized_paragraph_texts[i]

        # Clear existing runs in the paragraph
        # Iterate over a copy of the run elements as we modify the list
        for run_element in p._element.xpath('./w:r'):
            run_element.getparent().remove(run_element)

        # Add the anonymized text in a new run
        # This new run will have the default formatting of the paragraph or document
        if anonymized_text.strip(): # Add a run only if the modified text is not empty after strip
             p.add_run(anonymized_text)
        # If anonymized_text.strip() is empty, the paragraph will be empty (no runs)


    # Ensure output directory exists (already in original code, kept for robustness)
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Save the modified document
    doc.save(output_path)