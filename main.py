import os
import argparse # Importer le module argparse

from anonymizer.spacy_engine import SpaCyEngine
from anonymizer.word_processor import extract_text_from_docx, replace_entities_in_docx
from anonymizer.excel_processor import extract_text_from_excel, replace_entities_in_excel
from anonymizer.replacer import generate_replacements

# Configurer l'analyseur d'arguments
parser = argparse.ArgumentParser(description="Anonymise automatiquement des fichiers Word (.docx) et Excel (.xlsx).")
parser.add_argument("input_filename", help="Le nom du fichier à anonymiser (doit être dans le dossier input_files/).")

# Analyser les arguments de la ligne de commande
args = parser.parse_args()

# Utiliser le nom de fichier fourni en argument
input_filename = args.input_filename
input_path = os.path.join("input_files", input_filename)

# Déterminer le chemin de sortie basé sur le nom du fichier d'entrée
output_filename = f"{os.path.splitext(input_filename)[0]}_anonymise{os.path.splitext(input_filename)[1]}"
output_path = os.path.join("output_files", output_filename)

# Obtenir l'extension du fichier
file_extension = os.path.splitext(input_filename)[1].lower()

texte = None
entities = []
engine = SpaCyEngine() # Initialiser le moteur spaCy une seule fois

try:
    if not os.path.exists(input_path):
        print(f"Erreur : Le fichier d'entrée n'existe pas à l'emplacement {input_path}")
    else:
        # Extraire le texte en fonction du type de fichier
        if file_extension == ".docx":
            print(f"Traitement du fichier Word : {input_filename}")
            texte = extract_text_from_docx(input_path)
        elif file_extension == ".xlsx":
            print(f"Traitement du fichier Excel : {input_filename}")
            excel_data_list = extract_text_from_excel(input_path)
            texte = "\n".join(excel_data_list)
        else:
            print(f"Erreur : Type de fichier non supporté : {file_extension}")
            texte = None

        if texte is not None:
            # Détecter les entités dans le texte extrait
            print("Détection des entités...")
            entities = engine.detect_entities(texte)
            print(f"Entités détectées : {entities}")

            # Générer les remplacements
            replacements = generate_replacements(entities)
            print(f"Remplacements générés : {replacements}")

            # Remplacer les entités en fonction du type de fichier
            if file_extension == ".docx":
                print(f"Remplacement des entités dans le fichier Word...")
                replace_entities_in_docx(input_path, replacements, output_path)
                print("✅ Anonymisation terminée :", output_path)
            elif file_extension == ".xlsx":
                 print(f"Remplacement des entités dans le fichier Excel...")
                 replace_entities_in_excel(input_path, replacements, output_path)
                 print("✅ Anonymisation terminée :", output_path)

except Exception as e:
    print(f"Une erreur inattendue s'est produite : {e}")
