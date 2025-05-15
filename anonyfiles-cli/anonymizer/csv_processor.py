import csv
import os
from .utils import apply_positional_replacements # Importer la fonction de remplacement positionnel

def extract_text_from_csv(path):
    """Extrait le texte cellule par cellule depuis un fichier CSV (pour détection globale)."""
    cell_texts = []
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            cell_texts.extend(row)
    return cell_texts

# Modifier la signature pour accepter les données originales et les entités avec offsets par cellule
def replace_entities_in_csv(input_path, output_path, replacements, original_rows_data, entities_per_cell_with_offsets):
    """
    Remplace les entités dans un fichier CSV en utilisant le remplacement basé sur la position
    cellule par cellule.
    """
    # original_rows_data est déjà fourni, pas besoin de relire le fichier ici

    if not original_rows_data:
        # Créer un fichier CSV vide si les données originales sont vides
        with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
            pass
        return

    anonymized_rows = []
    cell_index_counter = 0 # Compteur pour suivre l'index des cellules plates

    for row in original_rows_data:
        new_row = []
        for cell in row:
            cell_text = str(cell) # S'assurer que le contenu de la cellule est une chaîne

            # Obtenir les entités avec offsets pour cette cellule spécifique en utilisant le compteur
            entities_for_this_cell = []
            if cell_index_counter < len(entities_per_cell_with_offsets):
                 entities_for_this_cell = entities_per_cell_with_offsets[cell_index_counter]

            if cell_text.strip() and entities_for_this_cell:
                # Appliquer le remplacement basé sur la position au texte de la cellule
                anonymized_text = apply_positional_replacements(
                    cell_text,
                    replacements, # Utiliser la table de remplacements globale
                    entities_for_this_cell # Utiliser les entités AVEC offsets pour cette cellule
                )
            else:
                # Si la cellule est vide ou ne contient pas d'entités à remplacer dans cette passe
                anonymized_text = cell_text # Conserver le texte original

            new_row.append(anonymized_text)
            cell_index_counter += 1 # Incrémenter le compteur de cellules

        anonymized_rows.append(new_row)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Écrire les données anonymisées dans le fichier CSV de sortie
    with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
        writer = csv.writer(fout)
        writer.writerows(anonymized_rows)