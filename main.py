from anonymizer.spacy_engine import SpaCyEngine
from anonymizer.word_processor import extract_text_from_docx, replace_entities_in_docx
from anonymizer.replacer import generate_replacements

input_path = "input_files/mon_fichier.docx"
output_path = "output_files/mon_fichier_anonymise.docx"

texte = extract_text_from_docx(input_path)
engine = SpaCyEngine()
entites = engine.detect_entities(texte)
replacements = generate_replacements(entites)
replace_entities_in_docx(input_path, replacements, output_path)

print("✅ Anonymisation terminée :", output_path)
