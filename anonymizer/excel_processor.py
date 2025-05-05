# Dans anonyfiles-main/anonymizer/excel_processor.py
import pandas as pd

def extract_text_from_excel(path):
    df = pd.read_excel(path)
    # Extrait le texte cellule par cellule, conserve l'idée d'une liste mais
    # l'analyse spaCy sera toujours faite sur la concaténation pour l'instant.
    # Une amélioration future pourrait traiter chaque cellule individuellement.
    cell_texts = []
    for row_index in range(df.shape[0]):
        for col_index in range(df.shape[1]):
            cell_value = df.iloc[row_index, col_index]
            if isinstance(cell_value, str):
                cell_texts.append(cell_value)
            # Vous pourriez aussi vouloir inclure d'autres types comme les nombres
            # si spaCy doit les analyser, mais spaCy se concentre sur les entités nommées.
            # elif pd.notna(cell_value): # Inclure les non-NaN non-strings
            #     cell_texts.append(str(cell_value))
    return cell_texts # Renvoie une liste de textes de cellules strings

def replace_entities_in_excel(path, replacements, output_path):
    df = pd.read_excel(path)

    # Itérer sur les cellules et appliquer les remplacements
    # Cette approche est plus précise car elle opère cellule par cellule
    for row_index in range(df.shape[0]):
        for col_index in range(df.shape[1]):
            cell_value = df.iloc[row_index, col_index]

            # Ne traiter que les cellules contenant du texte
            if isinstance(cell_value, str):
                new_cell_value = cell_value # Commence avec la valeur originale de la cellule

                # Appliquer chaque remplacement si l'original est trouvé dans la cellule
                for original, replacement in replacements.items():
                    if original in new_cell_value:
                        # Note : Comme pour Word, .replace() peut avoir des limites
                        # si l'original est une sous-chaîne d'une autre partie du texte dans la même cellule.
                        # Une solution parfaite nécessiterait de travailler avec les positions exactes.
                        new_cell_value = new_cell_value.replace(original, replacement)

                # Mettre à jour la cellule uniquement si des remplacements ont été effectués
                if new_cell_value != cell_value:
                    df.iloc[row_index, col_index] = new_cell_value

    df.to_excel(output_path, index=False)
