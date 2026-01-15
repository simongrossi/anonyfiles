# anonymizer/excel_processor.py

import pandas as pd
from pathlib import Path
import logging
from .base_processor import BaseProcessor
from .utils import apply_positional_replacements

logger = logging.getLogger(__name__)


class ExcelProcessor(BaseProcessor):
    """
    Processor pour les fichiers .xlsx (Excel).
    - Chaque cellule est un bloc.
    """

    def extract_blocks(self, input_path):
        """
        Extrait chaque cellule Excel comme un bloc (texte à plat, row-major).
        Retourne une liste à plat contenant chaque cellule (ligne après ligne).
        """
        df = pd.read_excel(input_path)
        cell_texts = []
        for row_index in range(df.shape[0]):
            for col_index in range(df.shape[1]):
                cell_value = df.iloc[row_index, col_index]
                cell_texts.append(str(cell_value) if pd.notna(cell_value) else "")
        return cell_texts

    def replace_entities(
        self, input_path, output_path, replacements, entities_per_block_with_offsets
    ):
        """
        Remplace les entités dans chaque cellule Excel et sauvegarde le résultat.
        """
        df = pd.read_excel(input_path)
        if df.empty:
            df.to_excel(output_path, index=False)
            return

        anonymized_df = df.copy()
        cell_index_counter = 0
        for row_index in range(anonymized_df.shape[0]):
            for col_index in range(anonymized_df.shape[1]):
                cell_value = anonymized_df.iloc[row_index, col_index]
                cell_text = str(cell_value) if pd.notna(cell_value) else ""
                entities_for_this_cell = []
                if cell_index_counter < len(entities_per_block_with_offsets):
                    entities_for_this_cell = entities_per_block_with_offsets[
                        cell_index_counter
                    ]
                if cell_text.strip() and entities_for_this_cell:
                    anonymized_text = apply_positional_replacements(
                        cell_text, replacements, entities_for_this_cell
                    )
                else:
                    anonymized_text = cell_text
                anonymized_df.iloc[row_index, col_index] = anonymized_text
                cell_index_counter += 1

        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        anonymized_df.to_excel(output_path, index=False)

    def reconstruct_and_write_anonymized_file(
        self, output_path, final_processed_blocks, original_input_path, **kwargs
    ):
        """Reconstruit un fichier Excel à partir des blocs traités et l'enregistre."""
        df = pd.read_excel(original_input_path)

        if df.empty:
            df.to_excel(output_path, index=False)
            return

        expected_count = int(df.shape[0] * df.shape[1])
        if expected_count != len(final_processed_blocks):
            logger.warning(
                "Mismatch entre %s cellules attendues et %s blocs fournis pour %s",
                expected_count,
                len(final_processed_blocks),
                output_path,
            )
            raise ValueError(
                f"Le nombre de cellules ({expected_count}) ne correspond pas au nombre de blocs finaux ({len(final_processed_blocks)})."
            )

        anonymized_df = df.copy()
        cell_index_counter = 0
        for row_index in range(anonymized_df.shape[0]):
            for col_index in range(anonymized_df.shape[1]):
                if cell_index_counter < len(final_processed_blocks):
                    anonymized_df.iloc[row_index, col_index] = final_processed_blocks[
                        cell_index_counter
                    ]
                cell_index_counter += 1

        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        anonymized_df.to_excel(output_path, index=False)
