# anonymizer/excel_processor.py

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from .base_processor import BaseProcessor
from .utils import apply_positional_replacements

logger = logging.getLogger(__name__)


class ExcelProcessor(BaseProcessor):
    """
    Processor pour les fichiers .xlsx (Excel).
    - Supporte le multi-feuilles : toutes les feuilles sont traitées.
    - Chaque cellule (pour chaque feuille) est un bloc.
    - Les données sont lues en STR pour éviter l'inférence de type (perte de '0' initial, etc.).
    """

    def __init__(self):
        super().__init__()
        # On va stocker ici les infos de chaque feuille (nom de feuille -> DataFrame original vide ou métadonnées)
        # Mais extract_blocks est souvent appelé sans persistence de l'instance entre l'extract et le write
        # dans une architecture 'stateless' pure.
        # CEPENDANT, AnonyfilesEngine instancie le processor à chaque fichier via la Factory.
        # Donc on peut stocker l'état dans self.sheets_metadata.
        self.sheets_metadata = {}  # {sheet_name: {'index': ..., 'columns': ..., 'shape': ...}}
        self.sheet_names_order = []

    def extract_blocks(self, input_path, **kwargs):
        """
        Extrait chaque cellule Excel comme un bloc (texte à plat, row-major).
        Lit TOUTES les feuilles. Force le type string pour préserver les données brutes (ex: numéros de téléphone).
        Retourne une liste à plat contenant toutes les cellules de toutes les feuilles.
        """
        # sheet_name=None -> Lit toutes les feuilles dans un dictionnaire {nom: df}
        # header=None -> On traite le header comme des données normales à anonymiser
        # dtype=str -> Crucial pour ne pas perdre les zéros initiaux (06...) ou corrompre les SIRET
        dfs = pd.read_excel(input_path, sheet_name=None, header=None, dtype=str)
        
        all_blocks = []
        self.sheets_metadata = {}
        self.sheet_names_order = []

        for sheet_name, df in dfs.items():
            # Remplacement des NaN par ""
            df = df.fillna("")
            
            # Stockage des métadonnées pour la reconstruction
            self.sheet_names_order.append(sheet_name)
            self.sheets_metadata[sheet_name] = {
                'shape': df.shape,
                'index': df.index,
                'columns': df.columns
            }
            
            # Aplatissement (row-major par défaut avec values.flatten())
            # flatten() retourne une copie 1D numpy array, tolist() en fait une liste python
            flat_values = df.values.flatten().tolist()
            all_blocks.extend(flat_values)

        return all_blocks

    def replace_entities(
        self, input_path, output_path, replacements, entities_per_block_with_offsets
    ):
        """
        [Legacy method - conservée pour compatibilité si nécessaire, mais engine préfère reconstruct...]
        Remplace les entités dans chaque cellule Excel et sauvegarde le résultat.
        """
        # Note: Cette méthode est moins optimale car elle doit relire le fichier.
        # Idéalement engine.py devrait utiliser reconstruct_and_write_anonymized_file.
        # Ici on réimplémente une logique similaire à reconstruct mais en refaisant tout.
        
        dfs = pd.read_excel(input_path, sheet_name=None, header=None, dtype=str)
        
        # On doit utiliser un writer pour supporter le multi-feuilles
        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)
            
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            global_block_index = 0
            
            for sheet_name, df in dfs.items():
                df = df.fillna("")
                anonymized_data = df.values.copy() # Numpy array
                
                rows, cols = anonymized_data.shape
                
                for r in range(rows):
                    for c in range(cols):
                        cell_text = str(anonymized_data[r, c])
                        
                        entities_for_this_cell = []
                        if global_block_index < len(entities_per_block_with_offsets):
                            entities_for_this_cell = entities_per_block_with_offsets[global_block_index]
                            
                        if cell_text.strip() and entities_for_this_cell:
                            anonymized_text = apply_positional_replacements(
                                cell_text, replacements, entities_for_this_cell
                            )
                            anonymized_data[r, c] = anonymized_text
                        
                        global_block_index += 1
                
                # Création du DF anonymisé
                new_df = pd.DataFrame(anonymized_data, index=df.index, columns=df.columns)
                new_df.to_excel(writer, sheet_name=sheet_name, header=False, index=False)


    def reconstruct_and_write_anonymized_file(
        self, output_path, final_processed_blocks, original_input_path, **kwargs
    ):
        """
        Reconstruit un fichier Excel complet (multi-feuilles) à partir des blocs traités.
        Utilise les métadonnées stockées lors de l'extraction ou relit le fichier si nécessaire.
        """
        
        # Si pour une raison quelconque self.sheets_metadata est vide (ex: redémarrage worker stateless pour la phase write ?),
        # il faudrait le re-populer. Dans le doute, on relit si vide.
        if not self.sheets_metadata:
            # Relecture pour la structure
            dfs = pd.read_excel(original_input_path, sheet_name=None, header=None, dtype=str)
            self.sheet_names_order = []
            for sheet_name, df in dfs.items():
                self.sheet_names_order.append(sheet_name)
                self.sheets_metadata[sheet_name] = {
                    'shape': df.shape,
                    'index': df.index,
                    'columns': df.columns
                }

        # Calcul global pour vérification
        total_cells_expected = sum(
            m['shape'][0] * m['shape'][1] for m in self.sheets_metadata.values()
        )
        
        if total_cells_expected != len(final_processed_blocks):
             logger.warning(
                "Mismatch Excel: %s cellules attendues vs %s blocs fournis. Ajustement...",
                total_cells_expected,
                len(final_processed_blocks)
            )
             # On ne lève pas d'erreur bloquante ici pour la robustesse, mais c'est risqué.
             # Si mismatch, on risque de décaler les données.
             # On va essayer de continuer tant qu'on a des blocs.

        output_dir = Path(output_path).parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        current_block_idx = 0
        
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                for sheet_name in self.sheet_names_order:
                    meta = self.sheets_metadata[sheet_name]
                    rows, cols = meta['shape']
                    count_cells = rows * cols
                    
                    # Extraction du chunk de blocs correspondant à cette feuille
                    chunk = final_processed_blocks[current_block_idx : current_block_idx + count_cells]
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
                    
                    new_df = pd.DataFrame(matrix_data, index=meta['index'], columns=meta['columns'])
                    
                    # write header=False car nous avons tout lu comme des données
                    new_df.to_excel(writer, sheet_name=sheet_name, header=False, index=False)
                    
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture Excel: {e}")
            raise e
