# anonymizer/txt_processor.py

import os
from .base_processor import BaseProcessor
from .utils import apply_positional_replacements

class TxtProcessor(BaseProcessor):
    """
    Processor pour les fichiers .txt.
    - Un seul bloc : tout le contenu du fichier.
    """

    def extract_blocks(self, input_path):
        """Extrait tout le texte du fichier comme un seul bloc."""
        with open(input_path, 'r', encoding='utf-8') as f:
            return [f.read()]  # Un seul bloc

    def replace_entities(
        self,
        input_path,
        output_path,
        replacements,
        entities_per_block_with_offsets
    ):
        """
        Remplace les entités dans le texte du fichier en utilisant les offsets
        puis écrit le résultat dans output_path.
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            text_content = f.read()

        # Si vide, copier le contenu tel quel (ou fichier vide)
        if not text_content.strip():
            with open(output_path, 'w', encoding='utf-8') as fout:
                fout.write(text_content)
            return

        # Utiliser la première (et unique) liste d'entités pour ce bloc
        entities_with_offsets = entities_per_block_with_offsets[0] if entities_per_block_with_offsets else []
        anonymized_text = apply_positional_replacements(
            text_content,
            replacements,
            entities_with_offsets
        )

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as fout:
            fout.write(anonymized_text)
