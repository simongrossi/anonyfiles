import pandas as pd
import os
from .utils import apply_positional_replacements  # Importer la fonction de remplacement positionnel

def extract_text_from_excel(path):
    """Extrait le texte cellule par cellule depuis un fichier Excel (pour détection globale)."""
    df = pd.read_excel(path)
    cell_texts = []
    # Itérer sur les cellules pour collecter le texte plat
    for row_index in range(df.shape[0]):
        for col_index in range(df.shape[1]):
            cell_value = df.iloc[row_index, col_index]
            cell_texts.append(str(cell_value) if pd.notna(cell_value) else '')
    return cell_texts

# Modifier la signature pour accepter le DataFrame original et les entités avec offsets par cellule
def replace_entities_in_excel(input_path, output_path, replacements, original_dataframe_data, entities_per_cell_with_offsets):
    """
    Remplace les entités dans un fichier Excel à l'aide de la table de remplacement
    en utilisant le remplacement basé sur la position cellule par cellule.
    """
    # original_dataframe_data est déjà fourni, pas besoin de relire le fichier ici
    df = original_dataframe_data.copy() # Travailler sur une copie du DataFrame original

    if df.empty:
        df.to_excel(output_path, index=False)
        return

    anonymized_df = df # anonymized_df est maintenant une copie sur laquelle on va modifier

    cell_index_counter = 0 # Compteur pour suivre l'index des cellules plates

    # Itérer sur les cellules du DataFrame
    for row_index in range(anonymized_df.shape[0]):
        for col_index in range(anonymized_df.shape[1]):
            cell_value = anonymized_df.iloc[row_index, col_index]
            cell_text = str(cell_value) if pd.notna(cell_value) else '' # S'assurer que le contenu est une chaîne

            # Obtenir les entités avec offsets pour cette cellule spécifique en utilisant le compteur
            entities_for_this_cell = []
            # S'assurer que l'index ne dépasse pas la taille de la liste d'entités fournies
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


            # Placer le texte anonymisé dans la cellule correspondante du DataFrame anonymisé
            anonymized_df.iloc[row_index, col_index] = anonymized_text
            cell_index_counter += 1 # Incrémenter le compteur de cellules


    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Écrire le DataFrame anonymisé dans le fichier Excel de sortie
    # index=False pour ne pas écrire l'index du DataFrame dans le fichier
    anonymized_df.to_excel(output_path, index=False)