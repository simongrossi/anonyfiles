# main.py
import os
import argparse
import csv
from datetime import datetime

from anonymizer.spacy_engine import SpaCyEngine
from anonymizer.word_processor import extract_text_from_docx, replace_entities_in_docx
from anonymizer.excel_processor import extract_text_from_excel, replace_entities_in_excel
from anonymizer.csv_processor import extract_text_from_csv, replace_entities_in_csv
from anonymizer.txt_processor import extract_text_from_txt, replace_entities_in_txt
from anonymizer.replacer import generate_replacements

parser = argparse.ArgumentParser(description="Anonymise automatiquement des fichiers Word, Excel, CSV et TXT.")
parser.add_argument("input_filename", help="Nom du fichier à anonymiser (dans le dossier input_files/).")
parser.add_argument("--log-entities", help="Chemin du fichier CSV pour exporter les entités détectées (optionnel).", default=None)
parser.add_argument("--entities", nargs='+', help="Liste des types d'entités à anonymiser (ex: PER LOC ORG DATE). Par défaut : toutes.", default=None)

args = parser.parse_args()

input_filename = args.input_filename
input_path = os.path.join("input_files", input_filename)
output_filename = f"{os.path.splitext(input_filename)[0]}_anonymise{os.path.splitext(input_filename)[1]}"
output_path = os.path.join("output_files", output_filename)
file_extension = os.path.splitext(input_filename)[1].lower()

entities = []
engine = SpaCyEngine()

try:
    if not os.path.exists(input_path):
        print(f"Erreur : Le fichier d'entrée n'existe pas à l'emplacement {input_path}")
    else:
        if file_extension == ".docx":
            print(f"Traitement du fichier Word : {input_filename}")
            text = extract_text_from_docx(input_path)
            print("Détection des entités dans le document...")
            ents = engine.detect_entities("\n".join(text))  # Traiter tout le texte en une seule fois
            entities.extend(ents)

        elif file_extension == ".xlsx":
            print(f"Traitement du fichier Excel : {input_filename}")
            text = extract_text_from_excel(input_path)
            ents = engine.detect_entities("\n".join(text))
            entities.extend(ents)

        elif file_extension == ".csv":
            print(f"Traitement du fichier CSV : {input_filename}")
            text = extract_text_from_csv(input_path)
            ents = engine.detect_entities("\n".join(text))
            entities.extend(ents)

        elif file_extension == ".txt":
            print(f"Traitement du fichier TXT : {input_filename}")
            text = extract_text_from_txt(input_path)
            ents = engine.detect_entities(text)  # Traiter tout le texte en une seule fois
            entities.extend(ents)

        else:
            print(f"Erreur : Type de fichier non supporté : {file_extension}")
            entities = []

        # --- Filtrer les entités si --entities est utilisé ---
        if args.entities:
            selected_labels = set(args.entities)
            print(f"Filtrage des entités avec les types : {selected_labels}")
            entities = [(text, label) for text, label in entities if label in selected_labels]

        if args.log_entities and entities:
            log_output_path = args.log_entities
            if os.path.dirname(log_output_path) == '':
                log_output_path = os.path.join('log', log_output_path)
            log_output_dir = os.path.dirname(log_output_path)
            if log_output_dir and not os.path.exists(log_output_dir):
                os.makedirs(log_output_dir, exist_ok=True)

            try:
                with open(log_output_path, mode='w', newline='', encoding='utf-8') as log_file:
                    log_writer = csv.writer(log_file)
                    log_writer.writerow(["Entite", "Label"])
                    for entity_text, entity_label in entities:
                        log_writer.writerow([entity_text, entity_label])
                print(f"✅ Entités détectées exportées vers : {log_output_path}")
            except Exception as log_e:
                print(f"Erreur lors de l'exportation des entités : {log_e}")

        if entities:
            print(f"Entités détectées : {entities}")
            replacements = generate_replacements(entities)
            print(f"Remplacements générés : {replacements}")

            if file_extension == ".docx":
                print("Remplacement des entités dans le fichier Word...")
                replace_entities_in_docx(input_path, replacements, output_path)
            elif file_extension == ".xlsx":
                print("Remplacement des entités dans le fichier Excel...")
                replace_entities_in_excel(input_path, replacements, output_path)
            elif file_extension == ".csv":
                print("Remplacement des entités dans le fichier CSV...")
                replace_entities_in_csv(input_path, replacements, output_path)
            elif file_extension == ".txt":
                print("Remplacement des entités dans le fichier TXT...")
                replace_entities_in_txt(input_path, replacements, output_path)
            print("✅ Anonymisation terminée :", output_path)
        elif file_extension in [".docx", ".xlsx", ".csv", ".txt"]:
            print("Aucune entité détectée. Aucun remplacement effectué.")

except FileNotFoundError:
    print(f"Erreur : Le fichier d'entrée n'a pas été trouvé à l'emplacement {input_path}")
except Exception as e:
    print(f"Une erreur inattendue s'est produite : {e}")
