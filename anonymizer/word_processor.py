# Dans anonyfiles-main/anonymizer/word_processor.py
from docx import Document

def extract_text_from_docx(path):
    doc = Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def replace_entities_in_docx(path, replacements, output_path):
    doc = Document(path)
    # Avertissement : La méthode de remplacement simple ci-dessous
    # peut ne pas gérer correctement les sous-chaînes ou la mise en forme complexe.
    # Une approche plus robuste nécessiterait de travailler avec les "runs"
    # ou la structure XML du document.
    for p in doc.paragraphs:
        for original, replacement in replacements.items():
            # Vérifier si l'entité originale existe dans le texte du paragraphe
            # Une amélioration potentielle, mais toujours basée sur du texte brut
            # et sujet aux problèmes de sous-chaînes/runs.
            if original in p.text:
                 # Note: Un remplacement simple de chaîne ici peut casser la mise en forme
                 # ou remplacer des parties de mots.
                 p.text = p.text.replace(original, replacement)
    doc.save(output_path)

# La fonction replace_entities_in_docx ci-dessus est conservée pour le moment,
# mais gardez à l'esprit sa limitation majeure.
# Un développement futur devrait se concentrer sur une méthode de remplacement
# plus précise au niveau de la structure du document.
