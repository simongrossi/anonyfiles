# anonymizer/base_processor.py
from typing import List, Dict, Any, Optional
from pathlib import Path

class BaseProcessor: #
    def extract_blocks(self, input_path: Path, **kwargs) -> List[str]: #
        raise NotImplementedError("extract_blocks doit être implémenté par la sous-classe.")

    def replace_entities( #
        self,
        input_path: Path, #
        output_path: Path, #
        replacements: Dict[str, str], #
        entities_per_block_with_offsets: List[List[Any]], #
        **kwargs 
    ):
        # Cette méthode sera appelée par l'engine pour les types de fichiers
        # où les règles custom ne sont pas (encore) gérées directement par l'engine.
        # Elle appliquera les remplacements spaCy.
        raise NotImplementedError("replace_entities doit être implémenté par la sous-classe.")

    def write_final_blocks(self, output_path: Path, 
                           final_anonymized_blocks: List[str], 
                           original_document_path_for_structure: Optional[Path] = None,
                           **kwargs):
        # Cette méthode est spécifique à la nouvelle approche pour TxtProcessor pour l'instant.
        # Les autres processeurs continueront d'utiliser replace_entities jusqu'à leur refactorisation.
        if isinstance(self, TxtProcessor): #
             # L'implémentation actuelle de TxtProcessor.write_final_blocks sera appelée.
             pass # ou lever NotImplementedError si on veut forcer chaque processeur à l'avoir.
        else:
            raise NotImplementedError(
                f"write_final_blocks n'est pas encore implémenté pour {self.__class__.__name__}. "
                f"L'engine devrait utiliser replace_entities pour ce type."
            )