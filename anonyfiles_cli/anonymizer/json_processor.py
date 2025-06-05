# anonyfiles_cli/anonymizer/json_processor.py

import json
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base_processor import BaseProcessor
# from .utils import apply_positional_replacements # Probablement plus nécessaire ici

logger = logging.getLogger(__name__)

class JsonProcessor(BaseProcessor):
    def extract_blocks(self, input_path: Path, **kwargs) -> List[str]:
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                return [f.read()]
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error("Erreur lors de la lecture de %s: %s", input_path, e)
            return [""]


    def reconstruct_and_write_anonymized_file(
        self,
        output_path: Path,
        final_processed_blocks: List[str], # Devrait contenir un seul élément pour JSON
        original_input_path: Path, # Non utilisé pour la reconstruction JSON simple
        **kwargs
    ) -> None:
        content_to_write = ""
        if final_processed_blocks:
            content_to_write = final_processed_blocks[0]
        else:
            logger.info(
                "INFO (JsonProcessor): Aucun bloc traité fourni pour %s, écriture d'un JSON vide (ou texte vide).",
                output_path,
            )
            # Pour un JSON, un contenu vide pourrait être "{}", "[]", ou juste "" selon la sémantique désirée.
            # Ici, on écrit ce que l'Engine a produit.

        output_dir = output_path.parent
        if not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        # Optionnel: Tenter de parser et réécrire en JSON formaté
        # Cela échouera si les remplacements ont cassé la structure JSON.
        try:
            parsed_json = json.loads(content_to_write)
            with open(output_path, 'w', encoding='utf-8') as fout:
                json.dump(parsed_json, fout, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            # Si ce n'est plus du JSON valide (par exemple, si des clés ont été anonymisées
            # d'une manière qui casse la structure), on écrit le texte tel quel.
            logger.warning(
                "AVERTISSEMENT (JsonProcessor): Le contenu pour %s n'est plus un JSON valide après traitement. Écriture en tant que texte brut.",
                output_path,
            )
            with open(output_path, 'w', encoding='utf-8') as fout:
                fout.write(content_to_write)

    # Ancienne méthode replace_entities (maintenant redondante pour le flux principal)
    # def replace_entities(self, input_path, output_path, replacements, entities_per_block_with_offsets):
    #     raise DeprecationWarning("JsonProcessor.replace_entities est obsolète.")
