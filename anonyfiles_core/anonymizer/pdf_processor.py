# anonymizer/pdf_processor.py

import fitz  # PyMuPDF
from pathlib import Path
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

    def replace_entities(
        self, input_path, output_path, replacements, entities_per_block_with_offsets
    ):
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

        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)

    def reconstruct_and_write_anonymized_file(
        self,
        output_path,
        final_processed_blocks,
        original_input_path,
        entities_per_block_with_offsets=None,
        **kwargs,
    ):
        """Reconstruit un PDF à partir des blocs traités."""
        original_doc = fitz.open(original_input_path)
        new_doc = fitz.open()

        if entities_per_block_with_offsets is None:
            entities_per_block_with_offsets = kwargs.get(
                "entities_per_block_with_offsets", []
            )

        for page_num, original_page in enumerate(original_doc):
            rect = original_page.rect
            new_page = new_doc.new_page(width=rect.width, height=rect.height)

            text = ""
            if page_num < len(final_processed_blocks):
                text = final_processed_blocks[page_num]

            new_page.insert_textbox(rect, text)

            if page_num < len(entities_per_block_with_offsets):
                entities = entities_per_block_with_offsets[page_num]
                for ent_text, ent_label, start, end in entities:
                    areas = new_page.search_for(ent_text)
                    for area in areas:
                        new_page.add_redact_annot(area, fill=(1, 1, 1))
                if entities:
                    new_page.apply_redactions()

        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        new_doc.save(output_path)
