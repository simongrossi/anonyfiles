# anonymizer/excel_processor.py

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Any
from .base_processor import BaseProcessor
from .type_defs import ExcelSheetMetadata, TextBlocks

logger = logging.getLogger(__name__)


class ExcelProcessor(BaseProcessor):
    """
    Processor pour les fichiers .xlsx (Excel).
    - Supporte le multi-feuilles : toutes les feuilles sont traitées.
    - Chaque cellule (pour chaque feuille) est un bloc.
    - Les données sont lues en STR pour éviter l'inférence de type (perte de '0' initial, etc.).
    """

    def __init__(self) -> None:
        super().__init__()
        # On va stocker ici les infos de chaque feuille (nom de feuille -> DataFrame original vide ou métadonnées)
        # Mais extract_blocks est souvent appelé sans persistence de l'instance entre l'extract et le write
        # dans une architecture 'stateless' pure.
        # CEPENDANT, AnonyfilesEngine instancie le processor à chaque fichier via la Factory.
        # Donc on peut stocker l'état dans self.sheets_metadata.
        self.sheets_metadata: dict[str, ExcelSheetMetadata] = {}
        self.sheet_names_order: list[str] = []

    def extract_blocks(self, input_path: Path, **kwargs: Any) -> TextBlocks:
        """
        Extrait chaque cellule Excel comme un bloc (texte à plat, row-major).
        Lit TOUTES les feuilles. Force le type string pour préserver les données brutes (ex: numéros de téléphone).
        Retourne une liste à plat contenant toutes les cellules de toutes les feuilles.
        """
        # sheet_name=None -> Lit toutes les feuilles dans un dictionnaire {nom: df}
        # header=None -> On traite le header comme des données normales à anonymiser
        # dtype=str -> Crucial pour ne pas perdre les zéros initiaux (06...) ou corrompre les SIRET
        dfs = pd.read_excel(input_path, sheet_name=None, header=None, dtype=str)

        all_blocks: TextBlocks = []
        self.sheets_metadata = {}
        self.sheet_names_order = []

        for sheet_name, df in dfs.items():
            # Remplacement des NaN par ""
            df = df.fillna("")

            # Stockage des métadonnées pour la reconstruction
            self.sheet_names_order.append(sheet_name)
            self.sheets_metadata[sheet_name] = {
                "shape": df.shape,
                "index": df.index,
                "columns": df.columns,
            }

            # Aplatissement (row-major par défaut avec values.flatten())
            # flatten() retourne une copie 1D numpy array, tolist() en fait une liste python
            flat_values = [str(value) for value in df.values.flatten().tolist()]
            all_blocks.extend(flat_values)

        return all_blocks

    def reconstruct_and_write_anonymized_file(
        self,
        output_path: Path,
        final_processed_blocks: TextBlocks,
        original_input_path: Path,
        **kwargs: Any,
    ) -> None:
        """
        Reconstruit un fichier Excel complet (multi-feuilles) à partir des blocs traités.
        Utilise les métadonnées stockées lors de l'extraction ou relit le fichier si nécessaire.
        """

        # Si pour une raison quelconque self.sheets_metadata est vide (ex: redémarrage worker stateless pour la phase write ?),
        # il faudrait le re-populer. Dans le doute, on relit si vide.
        if not self.sheets_metadata:
            # Relecture pour la structure
            dfs = pd.read_excel(
                original_input_path, sheet_name=None, header=None, dtype=str
            )
            self.sheet_names_order = []
            for sheet_name, df in dfs.items():
                self.sheet_names_order.append(sheet_name)
                self.sheets_metadata[sheet_name] = {
                    "shape": df.shape,
                    "index": df.index,
                    "columns": df.columns,
                }

        # Calcul global pour vérification
        total_cells_expected = sum(
            m["shape"][0] * m["shape"][1] for m in self.sheets_metadata.values()
        )

        if total_cells_expected != len(final_processed_blocks):
            # Désalignement = bug d'extraction/reconstruction. On échoue de façon
            # explicite plutôt que de produire un fichier décalé / partiellement
            # anonymisé (risque de fuite de données non anonymisées).
            raise ValueError(
                f"Mismatch Excel: {total_cells_expected} cellules attendues "
                f"vs {len(final_processed_blocks)} blocs fournis."
            )

        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        current_block_idx = 0

        try:
            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                for sheet_name in self.sheet_names_order:
                    meta = self.sheets_metadata[sheet_name]
                    rows, cols = meta["shape"]
                    count_cells = rows * cols

                    # Extraction du chunk de blocs correspondant à cette feuille
                    chunk = final_processed_blocks[
                        current_block_idx : current_block_idx + count_cells
                    ]
                    current_block_idx += count_cells

                    # Si le chunk est incomplet (cas d'erreur)
                    if len(chunk) < count_cells:
                        # Remplissage avec des chaînes vides pour éviter crash reshape
                        missing = count_cells - len(chunk)
                        chunk.extend([""] * missing)

                    # Reshape en matrice (DataFrame)
                    # np.array(chunk) crée un tableau 1D
                    # reshape((rows, cols)) le remet en 2D
                    matrix_data = np.array(chunk).reshape((rows, cols))

                    new_df = pd.DataFrame(
                        matrix_data, index=meta["index"], columns=meta["columns"]
                    )

                    # write header=False car nous avons tout lu comme des données
                    new_df.to_excel(
                        writer, sheet_name=sheet_name, header=False, index=False
                    )

        except Exception as e:
            logger.error("Erreur lors de l'écriture Excel: %s", e)
            raise
