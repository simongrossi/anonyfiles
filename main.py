import os
from anonymizer.spacy_engine import SpaCyEngine
from anonymizer.word_processor import extract_text_from_docx, replace_entities_in_docx
from anonymizer.excel_processor import extract_text_from_excel, replace_entities_in_excel # Importer les fonctions Excel
from anonymizer.replacer import generate_replacements

# Définir les chemins d'entrée et de sortie (pour l'instant en dur, à améliorer plus tard)
input_filename = "mon_fichier.docx" # Exemple : peut être modifié pour tester .xlsx
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
            # L'extraction Excel actuelle retourne une liste, vous pourriez vouloir adapter cela
            # ou traiter les entités différemment pour Excel.
            # Pour l'instant, nous allons simplement joindre les chaînes pour l'analyse spaCy.
            excel_data_list = extract_text_from_excel(input_path)
            texte = "\n".join(excel_data_list) # Concaténer le texte pour l'analyse
        else:
            print(f"Erreur : Type de fichier non supporté : {file_extension}")
            texte = None # Assurez-vous que texte est None si le type n'est pas supporté

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
                 # La fonction de remplacement Excel actuelle utilise applymap et replace()
                 # ce qui peut ne pas être optimal compte tenu de l'extraction aplatie.
                 # Une approche plus fine pour Excel pourrait être nécessaire ici.
                 replace_entities_in_excel(input_path, replacements, output_path)
                 print("✅ Anonymisation terminée :", output_path)
            # Le cas 'else' pour le type de fichier non supporté est déjà géré plus haut

except Exception as e:
    print(f"Une erreur inattendue s'est produite : {e}")
