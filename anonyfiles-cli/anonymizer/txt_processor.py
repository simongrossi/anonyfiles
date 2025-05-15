import os
from .utils import apply_positional_replacements  # Importer la fonction de remplacement positionnel

def extract_text_from_txt(path):
    """Extrait le texte complet d'un fichier .txt."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

# Modifier la signature pour accepter les entités avec offsets
def replace_entities_in_txt(input_path, output_path, replacements, entities_with_offsets):
    """
    Remplace les entités dans un fichier texte avec la table de remplacements
    en utilisant le remplacement basé sur la position.
    """
    text_content = extract_text_from_txt(input_path)

    if not text_content.strip():
        with open(input_path, 'r', encoding='utf-8') as fin, \
             open(output_path, 'w', encoding='utf-8') as fout:
            fout.write(text_content)
        return

    # Utiliser la fonction de remplacement basée sur la position au lieu du simple replace()
    anonymized_text_content = apply_positional_replacements(
        text_content,
        replacements,
        entities_with_offsets # Passer les entités avec leurs offsets
    )

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as fout:
        # Écrire le contenu anonymisé
        fout.write(anonymized_text_content)