# anonymizer/utils.py

def apply_positional_replacements(text, entity_replacements, entities_in_text_block):
    from io import StringIO
    output = StringIO()
    cursor = 0
    sorted_entities = sorted(entities_in_text_block, key=lambda x: x[2])
    for ent_text, ent_label, ent_start_char, ent_end_char in sorted_entities:
        original_entity_key = ent_text.strip()
        replacement = entity_replacements.get(original_entity_key, ent_text)
        output.write(text[cursor:ent_start_char])
        output.write(replacement)
        cursor = ent_end_char
    output.write(text[cursor:])
    return output.getvalue()
