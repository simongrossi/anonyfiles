# anonyfiles_cli/anonymizer/writer.py

import csv
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import aiofiles
import io

from .base_processor import BaseProcessor
from .pdf_processor import PdfProcessor  # Spécifique pour kwargs de PDF


class AnonymizedFileWriter:
    """
    Gère l'écriture des différents fichiers de sortie après anonymisation.
    """

    def __init__(self, dry_run: bool):
        self.dry_run = dry_run

    def write_anonymized_file(
        self,
        processor: BaseProcessor,
        output_path: Path,
        final_processed_blocks: List[str],
        original_input_path: Path,
        spacy_entities_per_block_with_offsets: Optional[
            List[List[Tuple[str, str, int, int]]]
        ] = None,
        **kwargs,
    ) -> None:
        """
        Écrit le fichier anonymisé en utilisant le processeur approprié.
        """
        if self.dry_run:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        processor_specific_kwargs = {**kwargs}
        if isinstance(processor, PdfProcessor):
            # Les entités avec offsets sont nécessaires pour les processeurs PDF/DOCX
            # qui les utilisent pour appliquer les "redactions" ou remplacements positionnels
            processor_specific_kwargs["entities_per_block_with_offsets"] = (
                spacy_entities_per_block_with_offsets
            )

        processor.reconstruct_and_write_anonymized_file(
            output_path=output_path,
            final_processed_blocks=final_processed_blocks,
            original_input_path=original_input_path,
            **processor_specific_kwargs,
        )

    async def write_anonymized_file_async(
        self,
        processor: BaseProcessor,
        output_path: Path,
        final_processed_blocks: List[str],
        original_input_path: Path,
        spacy_entities_per_block_with_offsets: Optional[
            List[List[Tuple[str, str, int, int]]]
        ] = None,
        **kwargs,
    ) -> None:
        if self.dry_run:
            return

        output_path.parent.mkdir(parents=True, exist_ok=True)

        processor_specific_kwargs = {**kwargs}
        if isinstance(processor, PdfProcessor):
            processor_specific_kwargs["entities_per_block_with_offsets"] = (
                spacy_entities_per_block_with_offsets
            )

        await processor.reconstruct_and_write_anonymized_file_async(
            output_path=output_path,
            final_processed_blocks=final_processed_blocks,
            original_input_path=original_input_path,
            **processor_specific_kwargs,
        )

    def write_log_entities_file(
        self, log_entities_path: Path, unique_spacy_entities: List[Tuple[str, str]]
    ) -> None:
        """
        Écrit le fichier CSV de log des entités détectées.
        """
        if self.dry_run:
            return

        log_entities_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_entities_path, "w", encoding="utf-8", newline="") as f_log:
            log_writer = csv.writer(f_log)
            log_writer.writerow(["Entite", "Label"])
            for text, label_str in unique_spacy_entities:
                log_writer.writerow([text, label_str])

    async def write_log_entities_file_async(
        self,
        log_entities_path: Path,
        unique_spacy_entities: List[Tuple[str, str]],
    ) -> None:
        if self.dry_run:
            return

        log_entities_path.parent.mkdir(parents=True, exist_ok=True)
        buf = io.StringIO()
        log_writer = csv.writer(buf)
        log_writer.writerow(["Entite", "Label"])
        for text, label_str in unique_spacy_entities:
            log_writer.writerow([text, label_str])
        async with aiofiles.open(
            log_entities_path, "w", encoding="utf-8", newline=""
        ) as f_log:
            await f_log.write(buf.getvalue())

    def write_mapping_file(
        self,
        mapping_output_path: Path,
        custom_replacements_mapping: Dict[str, str],
        mapping_dict_spacy: Dict[str, str],
        unique_spacy_entities: List[Tuple[str, str]],
    ) -> None:
        """
        Écrit le fichier CSV de mapping complet (règles custom + spaCy).
        """
        if self.dry_run:
            return

        mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(mapping_output_path, "w", encoding="utf-8", newline="") as f_map:
            map_writer = csv.writer(f_map)
            map_writer.writerow(["anonymized", "original", "label", "source"])

            # Ajouter les mappings des règles personnalisées
            for original, anonymized in custom_replacements_mapping.items():
                map_writer.writerow([anonymized, original, "CUSTOM", "custom_rule"])

            # Ajouter les mappings spaCy
            for original, code in mapping_dict_spacy.items():
                # Trouver le label pour l'entité spaCy
                label = next(
                    (lbl for txt, lbl in unique_spacy_entities if txt == original),
                    "UNKNOWN_SPACY_LABEL",
                )
                map_writer.writerow([code, original, label, "spacy"])

    async def write_mapping_file_async(
        self,
        mapping_output_path: Path,
        custom_replacements_mapping: Dict[str, str],
        mapping_dict_spacy: Dict[str, str],
        unique_spacy_entities: List[Tuple[str, str]],
    ) -> None:
        if self.dry_run:
            return

        mapping_output_path.parent.mkdir(parents=True, exist_ok=True)
        buf = io.StringIO()
        map_writer = csv.writer(buf)
        map_writer.writerow(["anonymized", "original", "label", "source"])
        for original, anonymized in custom_replacements_mapping.items():
            map_writer.writerow([anonymized, original, "CUSTOM", "custom_rule"])
        for original, code in mapping_dict_spacy.items():
            label = next(
                (lbl for txt, lbl in unique_spacy_entities if txt == original),
                "UNKNOWN_SPACY_LABEL",
            )
            map_writer.writerow([code, original, label, "spacy"])
        async with aiofiles.open(
            mapping_output_path, "w", encoding="utf-8", newline=""
        ) as f_map:
            await f_map.write(buf.getvalue())
