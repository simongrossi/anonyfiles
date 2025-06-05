# anonyfiles_cli/anonymizer/ner_processor.py

import re
from typing import List, Dict, Any, Tuple, Set
import typer

from .spacy_engine import SpaCyEngine
from .spacy_engine import EMAIL_REGEX, DATE_REGEX, PHONE_REGEX, IBAN_REGEX

class NERProcessor:
    """
    Détecte les entités nommées (NER) dans des blocs de texte en utilisant spaCy et des regex additionnelles.
    """
    def __init__(self, spacy_engine: SpaCyEngine, enabled_labels: Set[str], excluded_labels: Set[str]):
        self.spacy_engine = spacy_engine
        self.enabled_labels = enabled_labels
        self.excluded_labels = excluded_labels
        
        self.final_enabled_labels_for_spacy = self.enabled_labels - self.excluded_labels
        typer.echo(f"DEBUG (NERProcessor Init): Labels spaCy effectivement activés pour la détection : {self.final_enabled_labels_for_spacy}")

    def detect_entities_in_blocks(self, text_blocks: List[str]) -> Tuple[List[Tuple[str, str]], List[List[Tuple[str, str, int, int]]]]:
        """
        Détecte les entités dans une liste de blocs de texte.
        Retourne :
        1. Une liste de tuples (entity_text, label) de toutes les entités uniques détectées.
        2. Une liste de listes de tuples (entity_text, label, start_char, end_char) par bloc,
           incluant les offsets pour le remplacement positionnel.
        """
        all_unique_entities_across_blocks: Dict[str, Tuple[str, str]] = {} # {entity_text: (label, source_type)}
        spacy_entities_per_block_with_offsets: List[List[Tuple[str, str, int, int]]] = []

        regex_sources = {
            "EMAIL": EMAIL_REGEX,
            "DATE": DATE_REGEX,
            "PHONE": PHONE_REGEX,
            "IBAN": IBAN_REGEX
        }
        
        PRIORITY_REGEX_LABELS = {"EMAIL", "DATE", "PHONE", "IBAN"}

        for block_text in text_blocks:
            detected_entities_for_this_block: List[Tuple[str, str, int, int]] = [] # Cette variable est celle qui est remplie
            
            if block_text.strip():
                doc = self.spacy_engine.nlp_doc(block_text)
                
                # 1. Collecter toutes les entités spaCy pertinentes
                for ent in doc.ents:
                    if ent.label_ in self.final_enabled_labels_for_spacy:
                        detected_entities_for_this_block.append((ent.text, ent.label_, ent.start_char, ent.end_char))
                
                # 2. Collecter toutes les entités Regex pertinentes
                for label, pattern in regex_sources.items():
                    if label in self.final_enabled_labels_for_spacy:
                        for match in re.finditer(pattern, block_text, re.IGNORECASE if label == "DATE" else 0):
                            detected_entities_for_this_block.append((match.group(0), label, match.start(), match.end()))
                
                # 3. Nettoyer et dédupliquer les entités du bloc avec gestion de priorité
                processed_entities_for_this_block: List[Tuple[str, str, int, int]] = []
                best_entities_by_span: Dict[Tuple[int, int], Tuple[str, str]] = {}

                # La variable à trier est bien 'detected_entities_for_this_block'
                detected_entities_for_this_block.sort(key=lambda x: x[2]) 

                for ent_text, ent_label, start, end in detected_entities_for_this_block:
                    span = (start, end)
                    
                    if span in best_entities_by_span:
                        existing_text, existing_label = best_entities_by_span[span]
                        
                        if ent_label in PRIORITY_REGEX_LABELS and existing_label not in PRIORITY_REGEX_LABELS:
                            best_entities_by_span[span] = (ent_text, ent_label)
                    else:
                        best_entities_by_span[span] = (ent_text, ent_label)
                
                processed_entities_for_this_block = sorted(
                    [(text, label, start, end) for (start, end), (text, label) in best_entities_by_span.items()],
                    key=lambda x: x[2]
                )

                # Add to the global list of unique entities (for the mapping)
                for ent_text, ent_label, _, _ in processed_entities_for_this_block:
                    is_current_regex_label = ent_label in PRIORITY_REGEX_LABELS
                    
                    if ent_text not in all_unique_entities_across_blocks:
                        all_unique_entities_across_blocks[ent_text] = (ent_label, "initial")
                    else:
                        existing_label, _ = all_unique_entities_across_blocks[ent_text]
                        is_existing_regex_label = existing_label in PRIORITY_REGEX_LABELS
                        
                        if is_current_regex_label and not is_existing_regex_label:
                            all_unique_entities_across_blocks[ent_text] = (ent_label, "regex_override")
                
                spacy_entities_per_block_with_offsets.append(processed_entities_for_this_block)
            
        final_unique_entities_list = [(text, data[0]) for text, data in all_unique_entities_across_blocks.items()]
        
        return final_unique_entities_list, spacy_entities_per_block_with_offsets