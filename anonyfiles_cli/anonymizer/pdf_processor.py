# anonymizer/pdf_processor.py

import fitz  # PyMuPDF
import os
from .base_processor import BaseProcessor

class PdfProcessor(BaseProcessor):
    """
    Processor pour fichiers PDF utilisant les annotations de redaction.
    Chaque page est un bloc de texte.
    """

    def extract_blocks(self, input_path):
        doc = fitz.open(input_path)
        blocks = []
        for page in doc:
            text = page.get_text("text")
            blocks.append(text)
        return blocks

    def replace_entities(self, input_path, output_path, replacements, entities_per_block_with_offsets):
        doc = fitz.open(input_path)

        for page_num, page in enumerate(doc):
            if page_num >= len(entities_per_block_with_offsets):
                break
            entities = entities_per_block_with_offsets[page_num]
            if not entities:
                continue

            # Ajouter une annotation de redaction pour chaque occurrence d'entité
            for ent_text, ent_label, start, end in entities:
                areas = page.search_for(ent_text)
                for area in areas:
                    # Crée une annotation de redaction blanche (masque le contenu)
                    page.add_redact_annot(area, fill=(1, 1, 1))

            # Appliquer toutes les redactions sur la page
            page.apply_redactions()

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        doc.save(output_path)

    def reconstruct_and_write_anonymized_file(
        self,
        output_path,
        final_processed_blocks,
        original_input_path,
        entities_per_block_with_offsets=None,
        **kwargs
    ):
        """Reconstruit un PDF en appliquant les redactions basées sur les entités."""
        doc = fitz.open(original_input_path)

        if entities_per_block_with_offsets is None:
            entities_per_block_with_offsets = kwargs.get("entities_per_block_with_offsets", [])

        for page_num, page in enumerate(doc):
            if page_num >= len(entities_per_block_with_offsets):
                break
            entities = entities_per_block_with_offsets[page_num]
            if not entities:
                continue

            for ent_text, ent_label, start, end in entities:
                areas = page.search_for(ent_text)
                for area in areas:
                    page.add_redact_annot(area, fill=(1, 1, 1))

            page.apply_redactions()

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        doc.save(output_path)
