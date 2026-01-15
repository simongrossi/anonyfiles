# anonyfiles_cli/anonymizer/utils.py

from typing import List, Dict, Tuple
from io import StringIO  # Nécessaire pour la fonction


def apply_positional_replacements(
    text: str,
    entity_replacements: Dict[str, str],
    entities_in_text_block: List[Tuple[str, str, int, int]],
) -> str:
    """
    Applique les remplacements d'entités dans un bloc de texte en respectant leurs positions.
    Cette fonction gère les remplacements qui changent la longueur du texte.

    Args:
        text (str): Le bloc de texte original.
        entity_replacements (Dict[str, str]): Dictionnaire des remplacements où la clé est le texte original de l'entité
                                              et la valeur est le texte anonymisé.
        entities_in_text_block (List[Tuple[str, str, int, int]]): Liste des entités détectées dans ce bloc,
                                                                 incluant le texte de l'entité, son label,
                                                                 sa position de début et sa position de fin
                                                                 (par rapport au texte original).

    Returns:
        str: Le texte avec les entités remplacées.
    """
    output = StringIO()

    # Les entités doivent être triées par leur position de début pour garantir
    # que les remplacements sont appliqués de gauche à droite, sans affecter les offsets
    # des ent entités non encore traitées dans le texte original.
    sorted_entities = sorted(entities_in_text_block, key=lambda x: x[2])

    current_original_cursor = 0  # Ce curseur suit la position dans le *texte original*.

    for ent_text, ent_label, ent_start_char, ent_end_char in sorted_entities:
        # Le "pattern" utilisé dans le dictionnaire `entity_replacements` doit correspondre
        # exactement à `ent_text` tel qu'il a été détecté.
        original_entity_key = ent_text

        # Récupère la valeur de remplacement, ou utilise l'entité originale si pas de remplacement trouvé.
        replacement_value = entity_replacements.get(original_entity_key, ent_text)

        # 1. Écrire la partie du texte original *avant* l'entité actuelle.
        # Cette partie va de la position du curseur actuel jusqu'au début de l'entité.
        output.write(text[current_original_cursor:ent_start_char])

        # 2. Écrire la valeur de remplacement de l'entité.
        output.write(replacement_value)

        # 3. Mettre à jour le curseur pour la prochaine itération.
        # Le curseur avance jusqu'à la fin de l'entité *originale* dans le texte original.
        # Le fait que `replacement_value` ait une longueur différente n'impacte pas
        # la lecture des offsets des entités *suivantes* dans le texte original.
        current_original_cursor = ent_end_char

    # 4. Écrire le reste du texte après la dernière entité traitée.
    output.write(text[current_original_cursor:])

    return output.getvalue()
