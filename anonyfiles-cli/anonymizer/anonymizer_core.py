# anonymizer/anonymizer_core.py
from io import StringIO
from .spacy_engine import SpaCyEngine
from .replacer import generate_replacements # Assuming replacer.py is in the same directory

def apply_positional_replacements(text, entity_replacements, entities_in_text_block):
    """
    Applique les remplacements d'entités dans un bloc de texte en utilisant les positions.
    Args:
        text (str): Le bloc de texte original.
        entity_replacements (dict): Dictionnaire mappant le texte original des entités à leur remplacement.
        entities_in_text_block (list): Liste des entités détectées dans ce bloc de texte par spaCy,
                                       au format (ent.text, ent.label_, ent.start_char, ent.end_char).
                                       Les offsets doivent être relatifs au début de 'text'.
    Returns:
        str: Le bloc de texte avec les entités remplacées.
    """
    output = StringIO()
    cursor = 0

    # Sort entities by their start character for correct processing order
    sorted_entities = sorted(entities_in_text_block, key=lambda x: x[2]) # Sort by start_char (index 2)

    for ent_text, ent_label, ent_start_char, ent_end_char in sorted_entities:
        # Ensure the entity text from detection matches the key in replacements
        # This might need refinement if spaCy's text includes leading/trailing spaces
        # compared to the key in entity_replacements. Using .strip() for robustness.
        original_entity_key = ent_text.strip()

        if original_entity_key in entity_replacements:
            replacement = entity_replacements[original_entity_key]

            # Add text before the current entity
            output.write(text[cursor:ent_start_char])

            # Add the replacement text
            output.write(replacement)

            # Move the cursor past the current entity
            cursor = ent_end_char
        else:
             # If for some reason the entity isn't in replacements, write the original text
             # This case should ideally not happen if entity_replacements is generated
             # from all entities found.
             output.write(text[cursor:ent_end_char])
             cursor = ent_end_char


    # Add any remaining text after the last entity
    output.write(text[cursor:])

    return output.getvalue()


def collect_and_anonymize_text_blocks(text_blocks, spacy_engine):
    """
    Collecte toutes les entités de plusieurs blocs de texte, génère les remplacements,
    puis applique l'anonymisation basée sur la position à chaque bloc.
    Args:
        text_blocks (list): Liste de chaînes de caractères (les blocs de texte).
        spacy_engine (SpaCyEngine): Instance du moteur spaCy.
    Returns:
        list: Liste des blocs de texte anonymisés.
    """
    all_entities_for_replacements = []
    entities_per_block = [] # Store entities with offsets for each block

    # First pass: Detect all entities from all blocks to generate consistent replacements
    for block in text_blocks:
        if isinstance(block, str) and block.strip(): # Process non-empty string blocks
            doc = spacy_engine.nlp(block)
            block_entities = []
            for ent in doc.ents:
                 # Store entity text and label for replacement generation
                 all_entities_for_replacements.append((ent.text, ent.label_))
                 # Store detailed entity info for positional replacement (text, label, start, end)
                 block_entities.append((ent.text, ent.label_, ent.start_char, ent.end_char))
            entities_per_block.append(block_entities)
        else:
             # If the block is not a string or is empty/whitespace, keep it as is and store empty entity list
             entities_per_block.append([])


    # Generate a single set of replacements for all collected entities
    # Using a set to handle potential duplicate (text, label) pairs across blocks
    unique_entities = list(set(all_entities_for_replacements))
    entity_replacements = generate_replacements(unique_entities)

    # Second pass: Apply positional replacements to each block
    anonymized_text_blocks = []
    for i, block in enumerate(text_blocks):
        if isinstance(block, str) and block.strip():
            anonymized_block = apply_positional_replacements(block, entity_replacements, entities_per_block[i])
            anonymized_text_blocks.append(anonymized_block)
        else:
            # Keep non-string or empty blocks as they were
            anonymized_text_blocks.append(block)


    return anonymized_text_blocks