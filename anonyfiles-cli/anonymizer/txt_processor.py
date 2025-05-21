# anonymizer/txt_processor.py
import os
from pathlib import Path 
from typing import List, Dict, Any, Optional 
from .base_processor import BaseProcessor
from .utils import apply_positional_replacements # pour replace_entities

class TxtProcessor(BaseProcessor): #
    def extract_blocks(self, input_path: Path, **kwargs) -> List[str]: #
        with open(input_path, 'r', encoding='utf-8') as f: #
            return [f.read()] # Un seul bloc

    def replace_entities(self, input_path: Path, output_path: Path, 
                         replacements: Dict[str, str], 
                         entities_per_block_with_offsets: List[List[Any]], 
                         **kwargs): #
        # Cette méthode est maintenant principalement pour les types non-TXT via l'engine,
        # ou si on voulait appeler le TxtProcessor de manière autonome avec des offsets pré-calculés.
        with open(input_path, 'r', encoding='utf-8') as f: #
            text_content = f.read() #

        if not text_content.strip(): #
            # ... (écriture fichier vide)
            output_dir = os.path.dirname(output_path) #
            if output_dir and not os.path.exists(output_dir): #
                os.makedirs(output_dir, exist_ok=True) #
            with open(output_path, 'w', encoding='utf-8') as fout: #
                fout.write(text_content) #
            return

        # Pour TxtProcessor, entities_per_block_with_offsets aura un seul élément
        current_block_entities_with_offsets = entities_per_block_with_offsets[0] if entities_per_block_with_offsets else [] #
        
        anonymized_text = text_content # Commence avec le texte original (ou celui après custom rules si input_path était un temp)
        if current_block_entities_with_offsets : # Uniquement si des entités spaCy existent pour ce bloc
             anonymized_text = apply_positional_replacements( #
                text_content, 
                replacements, # Map des remplacements spaCy
                current_block_entities_with_offsets
            )

        output_dir = os.path.dirname(output_path) #
        if output_dir and not os.path.exists(output_dir): #
            os.makedirs(output_dir, exist_ok=True) #
        with open(output_path, 'w', encoding='utf-8') as fout: #
            fout.write(anonymized_text) #

    def write_final_blocks(self, output_path: Path, 
                           final_anonymized_blocks: List[str], 
                           original_document_path_for_structure: Optional[Path] = None, 
                           **kwargs):
        """
        Écrit le bloc de texte final (qui a subi TOUTES les transformations : custom + spaCy)
        dans le fichier de sortie. Pour TxtProcessor, il n'y a qu'un seul bloc.
        """
        content_to_write = final_anonymized_blocks[0] if final_anonymized_blocks else ""
        
        # La création du dossier parent est déjà faite par AnonyfilesEngine avant d'appeler cette méthode
        # output_dir = os.path.dirname(output_path)
        # if output_dir and not os.path.exists(output_dir):
        # os.makedirs(output_dir, exist_ok=True)
            
        with open(output_path, 'w', encoding='utf-8') as fout:
            fout.write(content_to_write)