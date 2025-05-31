# anonyfiles/anonyfiles_cli/anonymizer/utils.py

def apply_positional_replacements(text, entity_replacements, entities_in_text_block):
    from io import StringIO
    output = StringIO()
    cursor = 0
    sorted_entities = sorted(entities_in_text_block, key=lambda x: x[2])

    previous_end = 0

    for ent_text, ent_label, ent_start_char, ent_end_char in sorted_entities:
        original_entity_key = ent_text.strip()
        replacement_value = entity_replacements.get(original_entity_key, ent_text)

        # Écrit le texte entre la fin de l'entité précédente et le début de la suivante
        in_between = text[cursor:ent_start_char]

        # Si pas d'espace entre deux entités dans le texte original, on en injecte un artificiellement
        if not in_between and previous_end == cursor:
            output.write(' ')
        else:
            output.write(in_between)

        final_replacement_to_write = replacement_value

        if ent_text.endswith('\n') and not replacement_value.endswith('\n'):
            if ent_text.rstrip('\n') == original_entity_key:
                final_replacement_to_write += '\n'

        output.write(final_replacement_to_write)
        cursor = ent_end_char
        previous_end = ent_end_char

    output.write(text[cursor:])
    return output.getvalue()
