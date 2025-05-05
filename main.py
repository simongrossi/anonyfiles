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

texte = None # Cette variable ne contiendra plus le texte complet concaténé
entities = []
engine = SpaCyEngine() # Initialiser le moteur spaCy une seule fois

try:
    if not os.path.exists(input_path):
        print(f"Erreur : Le fichier d'entrée n'existe pas à l'emplacement {input_path}")
    else:
        # Extraire le texte en fonction du type de fichier
        if file_extension == ".docx":
            print(f"Traitement du fichier Word : {input_filename}")
            # Extraire le texte paragraphe par paragraphe pour l'analyse spaCy
            paragraphs = extract_text_from_docx(input_path).split("\n")
            print("Détection des entités par paragraphe...")
            entities = []
            for p in paragraphs:
                # Détecter les entités dans chaque paragraphe individuellement
                ents = engine.detect_entities(p)
                entities.extend(ents) # Ajouter les entités détectées à la liste globale

        elif file_extension == ".xlsx":
            print(f"Traitement du fichier Excel : {input_filename}")
            # Pour Excel, nous concaténons toujours le texte pour l'analyse globale
            excel_data_list = extract_text_from_excel(input_path)
            texte_excel = "\n".join(excel_data_list)
            print("Détection des entités...")
            entities = engine.detect_entities(texte_excel) # Analyse globale pour Excel

        else:
            print(f"Erreur : Type de fichier non supporté : {file_extension}")
            entities = [] # Aucune entité détectée si le type n'est pas supporté


        if entities: # Procéder uniquement si des entités ont été détectées
            print(f"Entités détectées : {entities}")

            # Générer les remplacements
            replacements = generate_replacements(entities)
            print(f"Remplacements générés : {replacements}")

            # Remplacer les entités en fonction du type de fichier
            if file_extension == ".docx":
                print(f"Remplacement des entités dans le fichier Word...")
                # La fonction de remplacement opère déjà paragraphe par paragraphe
                replace_entities_in_docx(input_path, replacements, output_path)
                print("✅ Anonymisation terminée :", output_path)
            elif file_extension == ".xlsx":
                 print(f"Remplacement des entités dans le fichier Excel...")
                 replace_entities_in_excel(input_path, replacements, output_path)
                 print("✅ Anonymisation terminée :", output_path)
            # Le cas 'else' pour le type de fichier non supporté est déjà géré plus haut
        elif file_extension in [".docx", ".xlsx"]: # Si aucun type supporté mais aucune entité détectée
             print("Aucune entité détectée. Aucun remplacement effectué.")
             # Optionnel: copier le fichier original vers le dossier de sortie s'il n'y a pas de modifications
             # import shutil
             # shutil.copy2(input_path, output_path)
             # print(f"✅ Fichier copié sans modifications : {output_path}")


except FileNotFoundError:
     print(f"Erreur : Le fichier d'entrée n'a pas été trouvé à l'emplacement {input_path}")
except Exception as e:
    print(f"Une erreur inattendue s'est produite : {e}")
