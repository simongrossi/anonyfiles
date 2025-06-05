# anonyfiles_cli/anonymizer/ner_processor.py

import re
from typing import List, Dict, Any, Tuple, Set
import typer

from .spacy_engine import SpaCyEngine
from .spacy_engine import EMAIL_REGEX, DATE_REGEX, PHONE_REGEX, IBAN_REGEX

class NERProcessor:
    # ... (unchanged __init__)

    def detect_entities_in_blocks(self, text_blocks: List[str]) -> Tuple[List[Tuple[str, str]], List[List[Tuple[str, str, int, int]]]]:
        all_unique_entities_across_blocks: Dict[str, Tuple[str, str]] = {} # {entity_text: (label, source_type)}
        spacy_entities_per_block_with_offsets: List[List[Tuple[str, str, int, int]]] = []

        regex_sources = {
            "EMAIL": EMAIL_REGEX,
            "DATE": DATE_REGEX,
            "PHONE": PHONE_REGEX,
            "IBAN": IBAN_REGEX
        }

        PRIORITY_REGEX_LABELS = {"EMAIL", "DATE", "PHONE", "IBAN"} # Labels prioritaires issus de regex

        for block_text in text_blocks:
            # Collecte brute de toutes les détections pour ce bloc, avec filtration initiale par enabled_labels
            raw_detected_entities_for_this_block: List[Tuple[str, str, int, int]] = []

            if block_text.strip():
                doc = self.spacy_engine.nlp_doc(block_text)

                # 1. Collecter entités spaCy (si le label est activé et non exclu)
                for ent in doc.ents:
                    if ent.label_ in self.final_enabled_labels_for_spacy: # Check if label is enabled and not excluded
                        raw_detected_entities_for_this_block.append((ent.text, ent.label_, ent.start_char, ent.end_char))

                # 2. Collecter entités Regex (si le label est activé et non exclu)
                for label, pattern in regex_sources.items():
                    if label in self.final_enabled_labels_for_spacy: # Check if label is enabled and not excluded
                        for match in re.finditer(pattern, block_text, re.IGNORECASE if label == "DATE" else 0):
                            raw_detected_entities_for_this_block.append((match.group(0), label, match.start(), match.end()))

            # 3. Nettoyer et dédupliquer les entités du bloc avec gestion de priorité
            # Utiliser un dictionnaire temporaire pour la déduplication et la priorisation au niveau du bloc
            # La clé sera un tuple (start_offset, end_offset) pour gérer les chevauchements
            # La valeur sera (entity_text, label)

            # Sortir les entités par leur span (début, fin)
            # Si deux entités ont le même span, ou se chevauchent, une décision doit être prise.
            # Simplifions: si un span chevauche, privilégiez celui qui a un label prioritaire.

            # Trie les entités par leur position de début, puis par leur label pour une priorité stable
            # (ex: EMAIL avant MISC si même début).
            # Ce tri peut être affiné si la priorité des labels n'est pas alphabétique.
            # Une meilleure approche est d'itérer et de choisir.

            processed_entities_for_this_block: List[Tuple[str, str, int, int]] = []

            # Créez une liste d'entités avec un score de priorité si nécessaire,
            # ou triez-les de manière à ce que les plus spécifiques viennent en premier.
            # Pour EMAIL vs MISC, EMAIL est plus spécifique.

            # Pour les entités avec des spans qui se chevauchent ou sont identiques,
            # on veut garder la plus spécifique (ex: EMAIL > MISC).
            # Une façon simple est d'utiliser une liste et de "supprimer" les entités moins prioritaires.

            # Sortir par ordre de début, puis par label pour la priorité
            # Si vous avez une hiérarchie de priorité non-alphabétique, une fonction key_priority pourrait être utile.
            # Ex: key_priority = lambda label: 0 if label == "EMAIL" else (1 if label == "DATE" else 2) # etc.
            # Puis sort: key=lambda x: (x[2], key_priority(x[1]))

            # Utilisons une approche qui construit la liste finale en évitant les redondances et en priorisant.

            # Dictionary to store the best entity for each character span (simplification)
            # Key: (start, end) tuple, Value: (entity_text, label)
            best_entities_by_span: Dict[Tuple[int, int], Tuple[str, str]] = {}

            # Iterate through raw detections, prioritizing based on label specificity
            # This simple loop prioritizes later detections if they are more specific (e.g. EMAIL over MISC)
            # It does not handle complex overlaps, but simple text matches where one is more specific.

            # Sort by start_char for consistent processing of overlaps
            raw_detected_entities_for_this_block.sort(key=lambda x: x[2])

            for ent_text, ent_label, start, end in raw_detected_entities_for_this_block:
                span = (start, end)

                # Check for overlaps with existing entities in best_entities_by_span
                # This is a simplified overlap check. For robust overlap resolution,
                # a dedicated algorithm (e.g., interval tree) is needed.
                # For now, we'll focus on exact span or if a more specific label replaces a less specific one.

                # If this exact span is already covered, check priority
                if span in best_entities_by_span:
                    existing_text, existing_label = best_entities_by_span[span]

                    # If current label is more specific (e.g., EMAIL is more specific than MISC)
                    # This assumes a pre-defined order of specificity (e.g., EMAIL > MISC)
                    # For simplicity, we can say if current is a PRIORITY_REGEX_LABEL and existing is not, update.
                    if ent_label in PRIORITY_REGEX_LABELS and existing_label not in PRIORITY_REGEX_LABELS:
                        best_entities_by_span[span] = (ent_text, ent_label)
                else:
                    # Add if not seen before
                    best_entities_by_span[span] = (ent_text, ent_label)

            # Convert best_entities_by_span back to a list of (text, label, start, end)
            # Sort by start offset for positional replacement later
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

                    # If current entity is a priority regex label AND existing entity is NOT a priority regex label
                    # OR if current is a priority regex label AND existing is also a priority regex label but current is "more" specific
                    # (this "more specific" needs definition, e.g., hardcoded order or length etc.)
                    # For now, if current is priority regex and existing is not, then update.
                    if is_current_regex_label and not is_existing_regex_label:
                        all_unique_entities_across_blocks[ent_text] = (ent_label, "regex_override")

            spacy_entities_per_block_with_offsets.append(processed_entities_for_this_block)

        # Convert the global dictionary to final list of (text, label)
        final_unique_entities_list = [(text, data[0]) for text, data in all_unique_entities_across_blocks.items()]

        return final_unique_entities_list, spacy_entities_per_block_with_offsets