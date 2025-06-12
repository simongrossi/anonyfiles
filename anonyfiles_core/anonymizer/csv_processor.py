# anonyfiles_cli/anonymizer/csv_processor.py

import csv
import os
from pathlib import Path  # Corrected: Removed invalid non-printable character
from typing import List
from .base_processor import BaseProcessor
import aiofiles
import io
import logging

logger = logging.getLogger(__name__)
# apply_positional_replacements n'est plus nécessaire ici car le traitement se fait dans anonyfiles_core

class CsvProcessor(BaseProcessor):
    """
    Processor pour les fichiers .csv.
    - Chaque cellule est considérée comme un bloc.
    - Ne touche jamais l'entête (header) si présent.
    """

    def extract_blocks(self, input_path: Path, **kwargs) -> List[str]:
        """
        Extrait chaque cellule du CSV comme un bloc de texte à traiter.
        Retourne une liste à plat contenant toutes les cellules de données (pas de header si has_header=True).
        L'option 'has_header' est récupérée via kwargs.
        """
        has_header = kwargs.get('has_header', False)
        cell_texts: List[str] = []
        try:
            with open(input_path, mode='r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                for i, row in enumerate(reader):
                    if has_header and i == 0:
                        # Saute la ligne d'en-tête pour l'extraction des blocs
                        continue
                    cell_texts.extend(str(cell) for cell in row)
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Erreur lors de l'extraction des blocs du CSV %s: %s",
                input_path,
                e,
            )
            return []
        return cell_texts

    async def extract_blocks_async(self, input_path: Path, **kwargs) -> List[str]:
        has_header = kwargs.get('has_header', False)
        cell_texts: List[str] = []
        try:
            async with aiofiles.open(input_path, mode='r', encoding='utf-8', newline='') as f:
                content = await f.read()
            reader = csv.reader(io.StringIO(content))
            for i, row in enumerate(reader):
                if has_header and i == 0:
                    continue
                cell_texts.extend(str(cell) for cell in row)
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(
                "Erreur lors de l'extraction des blocs du CSV %s: %s",
                input_path,
                e,
            )
            return []
        return cell_texts

    def reconstruct_and_write_anonymized_file(
        self,
        output_path: Path,
        final_processed_blocks: List[str],
        original_input_path: Path,
        **kwargs
    ) -> None:
        """
        Reconstruit le fichier CSV en utilisant les blocs de texte (cellules) finalisés
        et l'écrit dans output_path.
        """
        has_header = kwargs.get('has_header', False)
        anonymized_rows: List[List[str]] = []
        original_row_structures: List[int] = []
        header_row: List[str] = []

        try:
            with open(original_input_path, mode='r', encoding='utf-8', newline='') as f_orig:
                reader_orig = csv.reader(f_orig)
                if has_header:
                    try:
                        header_row = next(reader_orig)
                        anonymized_rows.append(list(header_row))
                    except StopIteration:
                        pass

                for row_orig in reader_orig:
                    original_row_structures.append(len(row_orig))
        except FileNotFoundError:
            logger.error(
                "Erreur critique : Fichier original %s non trouvé lors de la reconstruction.",
                original_input_path,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                pass
            return
        except Exception as e:
            logger.error(
                "Erreur lors de la lecture du fichier CSV original %s pour reconstruction : %s",
                original_input_path,
                e,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                if header_row:
                    writer = csv.writer(fout)
                    writer.writerow(header_row)
            return

        current_block_index = 0
        for num_cols_in_original_row in original_row_structures:
            if current_block_index + num_cols_in_original_row > len(final_processed_blocks):
                logger.warning(
                    "Pas assez de blocs traités pour reconstruire la ligne avec %s colonnes. Index actuel: %s, Blocs restants: %s",
                    num_cols_in_original_row,
                    current_block_index,
                    len(final_processed_blocks) - current_block_index,
                )
                actual_cols_to_take = min(num_cols_in_original_row, len(final_processed_blocks) - current_block_index)
                new_row = final_processed_blocks[current_block_index : current_block_index + actual_cols_to_take]
                new_row.extend([""] * (num_cols_in_original_row - actual_cols_to_take))
            else:
                new_row = final_processed_blocks[current_block_index : current_block_index + num_cols_in_original_row]

            anonymized_rows.append(new_row)
            current_block_index += num_cols_in_original_row

        if current_block_index < len(final_processed_blocks):
            logger.warning(
                "%s blocs traités n'ont pas été utilisés dans la reconstruction du CSV.",
                len(final_processed_blocks) - current_block_index,
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                writer = csv.writer(fout)
                writer.writerows(anonymized_rows)
        except Exception as e:
            logger.error(
                "Erreur lors de l'écriture du fichier CSV anonymisé %s: %s",
                output_path,
                e,
            )

    async def reconstruct_and_write_anonymized_file_async(
        self,
        output_path: Path,
        final_processed_blocks: List[str],
        original_input_path: Path,
        **kwargs,
    ) -> None:
        has_header = kwargs.get('has_header', False)
        anonymized_rows: List[List[str]] = []
        original_row_structures: List[int] = []
        header_row: List[str] = []

        try:
            async with aiofiles.open(original_input_path, mode='r', encoding='utf-8', newline='') as f_orig:
                content = await f_orig.read()
            reader_orig = csv.reader(io.StringIO(content))
            if has_header:
                try:
                    header_row = next(reader_orig)
                    anonymized_rows.append(list(header_row))
                except StopIteration:
                    pass

            for row_orig in reader_orig:
                original_row_structures.append(len(row_orig))
        except FileNotFoundError:
            logger.error(
                "Erreur critique : Fichier original %s non trouvé lors de la reconstruction.",
                original_input_path,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                pass
            return
        except Exception as e:
            logger.error(
                "Erreur lors de la lecture du fichier CSV original %s pour reconstruction : %s",
                original_input_path,
                e,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            async with aiofiles.open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                if header_row:
                    buf = io.StringIO()
                    writer = csv.writer(buf)
                    writer.writerow(header_row)
                    await fout.write(buf.getvalue())
            return

        current_block_index = 0
        for num_cols_in_original_row in original_row_structures:
            if current_block_index + num_cols_in_original_row > len(final_processed_blocks):
                logger.warning(
                    "Pas assez de blocs traités pour reconstruire la ligne avec %s colonnes. Index actuel: %s, Blocs restants: %s",
                    num_cols_in_original_row,
                    current_block_index,
                    len(final_processed_blocks) - current_block_index,
                )
                actual_cols_to_take = min(num_cols_in_original_row, len(final_processed_blocks) - current_block_index)
                new_row = final_processed_blocks[current_block_index : current_block_index + actual_cols_to_take]
                new_row.extend([""] * (num_cols_in_original_row - actual_cols_to_take))
            else:
                new_row = final_processed_blocks[current_block_index : current_block_index + num_cols_in_original_row]

            anonymized_rows.append(new_row)
            current_block_index += num_cols_in_original_row

        if current_block_index < len(final_processed_blocks):
            logger.warning(
                "%s blocs traités n'ont pas été utilisés dans la reconstruction du CSV.",
                len(final_processed_blocks) - current_block_index,
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerows(anonymized_rows)
            async with aiofiles.open(output_path, mode='w', encoding='utf-8', newline='') as fout:
                await fout.write(csv_buffer.getvalue())
        except Exception as e:
            logger.error(
                "Erreur lors de l'écriture du fichier CSV anonymisé %s: %s",
                output_path,
                e,
            )
