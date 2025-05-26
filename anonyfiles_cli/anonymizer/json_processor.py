# anonymizer/json_processor.py

import json
import os
from .base_processor import BaseProcessor
from .utils import apply_positional_replacements

class JsonProcessor(BaseProcessor):
    """
    Processor pour fichiers JSON.
    Considère le JSON sérialisé en une seule chaîne (un seul bloc).
    """

    def extract_blocks(self, input_path):
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
        return [content]

    def replace_entities(self, input_path, output_path, replacements, entities_per_block_with_offsets):
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        entities = entities_per_block_with_offsets[0] if entities_per_block_with_offsets else []
        if not content.strip() or not entities:
            with open(output_path, "w", encoding="utf-8") as fout:
                fout.write(content)
            return

        new_content = apply_positional_replacements(content, replacements, entities)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fout:
            fout.write(new_content)
