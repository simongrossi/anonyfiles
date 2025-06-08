# anonymizer/base_processor.py
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio

class BaseProcessor:
    def extract_blocks(self, input_path: Path, **kwargs) -> List[str]:
        """
        Extrait les blocs de texte bruts du fichier d'entrée.
        Chaque chaîne de la liste représente une unité de texte à traiter
        (ex: un paragraphe, une cellule, une page, ou le fichier entier).
        """
        raise NotImplementedError("extract_blocks doit être implémenté par la sous-classe.")

    def reconstruct_and_write_anonymized_file(
        self,
        output_path: Path,
        final_processed_blocks: List[str], # Blocs après règles custom ET remplacements spaCy
        original_input_path: Path, # Pour la structure du fichier original si besoin (DOCX, PDF, en-têtes CSV)
        # **kwargs peut contenir des options spécifiques au processeur,
        # par exemple 'has_header' pour CsvProcessor,
        # ou 'spacy_entities_on_custom_text_per_block' pour PdfProcessor si nécessaire
        **kwargs
    ) -> None:
        """
        Reconstruit le fichier dans son format d'origine en utilisant les blocs de texte
        finalement traités et l'écrit dans output_path.
        """
        raise NotImplementedError("reconstruct_and_write_anonymized_file doit être implémenté par la sous-classe.")

    # Les anciennes méthodes comme 'replace_entities' ou 'write_final_blocks' (pour TxtProcessor)
    # peuvent être marquées comme obsolètes ou supprimées si elles ne sont plus appelées
    # directement par l'AnonyfilesEngine dans le nouveau flux.
    # Exemple :
    # def replace_entities(self, *args, **kwargs):
    #     raise DeprecationWarning(f"{self.__class__.__name__}.replace_entities est obsolète. Utiliser reconstruct_and_write_anonymized_file.")

    async def extract_blocks_async(self, input_path: Path, **kwargs) -> List[str]:
        """Asynchronous wrapper calling :meth:`extract_blocks` in a thread."""
        return await asyncio.to_thread(self.extract_blocks, input_path, **kwargs)

    async def reconstruct_and_write_anonymized_file_async(
        self,
        output_path: Path,
        final_processed_blocks: List[str],
        original_input_path: Path,
        **kwargs,
    ) -> None:
        """Asynchronous wrapper calling :meth:`reconstruct_and_write_anonymized_file` in a thread."""
        await asyncio.to_thread(
            self.reconstruct_and_write_anonymized_file,
            output_path,
            final_processed_blocks,
            original_input_path,
            **kwargs,
        )
