# anonymizer/txt_processor.py
import os # S'assurer que os est importé
from pathlib import Path
from typing import List, Dict, Any, Optional # Assurez-vous que Dict, Any, Optional sont là si vous les utilisez dans les signatures

from .base_processor import BaseProcessor
# from .utils import apply_positional_replacements # Probablement plus nécessaire ici directement

class TxtProcessor(BaseProcessor):
    def extract_blocks(self, input_path: Path, **kwargs) -> List[str]:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                return [f.read()]
        except FileNotFoundError:
            # Le moteur AnonyfilesEngine devrait idéalement vérifier l'existence du fichier
            # avant d'appeler extract_blocks, mais une gestion ici est une sécurité.
            # Cependant, la logique actuelle de l'Engine gère déjà les fichiers vides
            # ou les problèmes avant d'arriver ici massivement.
            # Pour un fichier non trouvé, une exception est plus appropriée pour remonter.
            raise
        except Exception as e:
            # Log l'erreur et retourne une liste avec un bloc vide pour éviter de planter
            # si on veut que le programme continue malgré tout (discutable)
            print(f"Erreur lors de la lecture de {input_path}: {e}")
            return [""]


    def reconstruct_and_write_anonymized_file(
        self,
        output_path: Path,
        final_processed_blocks: List[str], # Devrait contenir un seul élément pour TXT
        original_input_path: Path, # Non spécifiquement utilisé pour la reconstruction TXT simple
        **kwargs
    ) -> None:
        content_to_write = ""
        if final_processed_blocks: # S'assurer que la liste n'est pas vide
            content_to_write = final_processed_blocks[0]
        else:
            # Cas où le fichier original était vide ou les règles ont tout supprimé,
            # et l'Engine a passé une liste vide.
            print(f"INFO (TxtProcessor): Aucun bloc traité fourni pour {output_path}, écriture d'un fichier vide.")

        output_dir = output_path.parent # Utiliser output_path.parent pour le dossier
        if not output_dir.exists(): # S'assurer que le dossier de sortie existe
            output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as fout:
            fout.write(content_to_write)
