# anonymizer/csv_processor.py

import csv
import os
from .base_processor import BaseProcessor
from .utils import apply_positional_replacements

class CsvProcessor(BaseProcessor):
    """
    Processor pour les fichiers .csv.
    - Chaque cellule est considérée comme un bloc.
    """

    def extract_blocks(self, input_path):
        """
        Extrait chaque cellule du CSV comme un bloc de texte à traiter.
        Retourne une liste à plat contenant toutes les cellules (par lignes puis colonnes).
        """
        cell_texts = []
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                cell_texts.extend(row)
        return cell_texts

    def replace_entities(
        self,
        input_path,
        output_path,
        replacements,
        entities_per_block_with_offsets
    ):
        """
        Remplace les entités dans chaque cellule du CSV et écrit le résultat dans output_path.
        """
        original_rows_data = []
        with open(input_path, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                original_rows_data.append([str(cell) for cell in row])

        if not original_rows_data:
            # Fichier CSV vide
            with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                pass
            return

        anonymized_rows = []
        cell_index_counter = 0
        for row in original_rows_data:
            new_row = []
            for cell in row:
                cell_text = str(cell)
                entities_for_this_cell = []
                if cell_index_counter < len(entities_per_block_with_offsets):
                    entities_for_this_cell = entities_per_block_with_offsets[cell_index_counter]
                if cell_text.strip() and entities_for_this_cell:
                    anonymized_text = apply_positional_replacements(
                        cell_text,
                        replacements,
                        entities_for_this_cell
                    )
                else:
                    anonymized_text = cell_text
                new_row.append(anonymized_text)
                cell_index_counter += 1
            anonymized_rows.append(new_row)

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
            writer = csv.writer(fout)
            writer.writerows(anonymized_rows)
