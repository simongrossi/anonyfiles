# anonymizer/pdf_processor.py

import fitz  # PyMuPDF
from pathlib import Path
from typing import Any, Iterable
from .base_processor import BaseProcessor
from .type_defs import EntitySpansByBlock, ReplacementMap, TextBlocks


class PdfProcessor(BaseProcessor):
    """
    Processor pour fichiers PDF utilisant les annotations de redaction.
    Chaque page est un bloc de texte.
    """

    def extract_blocks(self, input_path: Path, **kwargs: Any) -> TextBlocks:
        doc = fitz.open(input_path)
        try:
            blocks: TextBlocks = []
            for page in doc:
                text = page.get_text("text")
                blocks.append(text)
            return blocks
        finally:
            doc.close()

    def reconstruct_and_write_anonymized_file(
        self,
        output_path: Path,
        final_processed_blocks: TextBlocks,
        original_input_path: Path,
        entities_per_block_with_offsets: EntitySpansByBlock | None = None,
        **kwargs: Any,
    ) -> None:
        """Reconstruit un PDF à partir des blocs traités."""
        if entities_per_block_with_offsets is None:
            entities_per_block_with_offsets = kwargs.get(
                "entities_per_block_with_offsets", []
            )

        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        replacement_map = self._build_replacement_map(
            kwargs.get("custom_replacements_mapping"),
            kwargs.get("spacy_replacements_map"),
            kwargs.get("replacements_map_spacy"),
        )
        if replacement_map:
            self._redact_original_pdf(
                output_path=output_path,
                original_input_path=original_input_path,
                entities_per_block_with_offsets=entities_per_block_with_offsets,
                replacement_map=replacement_map,
            )
            return

        self._reconstruct_text_pdf(
            output_path=output_path,
            final_processed_blocks=final_processed_blocks,
            original_input_path=original_input_path,
        )

    def _build_replacement_map(
        self,
        custom_replacements_mapping: ReplacementMap | None,
        spacy_replacements_map: ReplacementMap | None,
        legacy_spacy_replacements_map: ReplacementMap | None,
    ) -> ReplacementMap:
        replacement_map: ReplacementMap = {}
        for source in (
            custom_replacements_mapping,
            spacy_replacements_map,
            legacy_spacy_replacements_map,
        ):
            if not isinstance(source, dict):
                continue
            for original, replacement in source.items():
                if original and replacement is not None:
                    replacement_map[str(original)] = str(replacement)
        return replacement_map

    def _redact_original_pdf(
        self,
        output_path: Path,
        original_input_path: Path,
        entities_per_block_with_offsets: EntitySpansByBlock | None,
        replacement_map: ReplacementMap,
    ) -> None:
        doc = fitz.open(original_input_path)
        try:
            for page_num, page in enumerate(doc):
                page_pairs = self._replacement_pairs_for_page(
                    page_num, entities_per_block_with_offsets, replacement_map
                )
                redacted_areas: list[fitz.Rect] = []
                for original_text, replacement_text in page_pairs:
                    for area in page.search_for(original_text):
                        rect = fitz.Rect(area)
                        if self._intersects_existing_redaction(rect, redacted_areas):
                            continue
                        page.add_redact_annot(
                            rect,
                            text=replacement_text,
                            fontname="helv",
                            fontsize=self._replacement_font_size(rect),
                            fill=(1, 1, 1),
                            text_color=(0, 0, 0),
                            cross_out=False,
                        )
                        redacted_areas.append(rect)
                if redacted_areas:
                    page.apply_redactions()
            self._assert_no_sensitive_text_remains(doc, replacement_map)
            doc.save(output_path, garbage=4, deflate=True, clean=True)
        finally:
            doc.close()

    def _replacement_pairs_for_page(
        self,
        page_num: int,
        entities_per_block_with_offsets: EntitySpansByBlock | None,
        replacement_map: ReplacementMap,
    ) -> list[tuple[str, str]]:
        pairs: ReplacementMap = {}
        if entities_per_block_with_offsets and page_num < len(
            entities_per_block_with_offsets
        ):
            for ent_text, _ent_label, _start, _end in entities_per_block_with_offsets[
                page_num
            ]:
                replacement = replacement_map.get(ent_text)
                if replacement is not None:
                    pairs[ent_text] = replacement

        for original_text, replacement in replacement_map.items():
            pairs.setdefault(original_text, replacement)

        return sorted(pairs.items(), key=lambda item: len(item[0]), reverse=True)

    def _intersects_existing_redaction(
        self, rect: fitz.Rect, redacted_areas: Iterable[fitz.Rect]
    ) -> bool:
        return any(rect.intersects(existing) for existing in redacted_areas)

    def _replacement_font_size(self, rect: fitz.Rect) -> float:
        return max(4.0, min(11.0, rect.height * 0.7))

    def _assert_no_sensitive_text_remains(
        self, doc: fitz.Document, replacement_map: ReplacementMap
    ) -> None:
        remaining_text = "\n".join(page.get_text("text") for page in doc)
        leaked_values = sorted(
            {
                original_text
                for original_text in replacement_map
                if original_text and original_text in remaining_text
            }
        )
        if leaked_values:
            preview = ", ".join(repr(value) for value in leaked_values[:5])
            raise ValueError(
                "Redaction PDF incomplète: texte sensible encore extractible "
                f"({preview})."
            )

    def _reconstruct_text_pdf(
        self,
        output_path: Path,
        final_processed_blocks: TextBlocks,
        original_input_path: Path,
    ) -> None:
        original_doc = fitz.open(original_input_path)
        new_doc = fitz.open()
        try:
            for page_num, original_page in enumerate(original_doc):
                rect = original_page.rect
                new_page = new_doc.new_page(width=rect.width, height=rect.height)
                text = ""
                if page_num < len(final_processed_blocks):
                    text = final_processed_blocks[page_num]
                new_page.insert_textbox(rect, text)
            new_doc.save(output_path)
        finally:
            new_doc.close()
            original_doc.close()
