# anonyfiles_cli/anonymizer/replacement_generator.py

from typing import List, Dict, Any, Tuple

from .replacer import ReplacementSession
from .audit import AuditLogger


class ReplacementGenerator:
    """
    Génère les mappings de remplacement pour les entités spaCy détectées
    et les journalise dans l'audit logger.
    """

    def __init__(self, config: Dict[str, Any], audit_logger: AuditLogger):
        self.config = config
        self.audit_logger = audit_logger
        self.replacement_rules_spacy_config = self.config.get("replacements", {})
        self.session = ReplacementSession()

    def generate_spacy_replacements(
        self,
        unique_spacy_entities: List[Tuple[str, str]],
        entities_per_block_with_offsets: List[List[Tuple[str, str, int, int]]],
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Génère les remplacements pour les entités spaCy et met à jour l'audit log.
        Retourne le dictionnaire des remplacements (original_text -> anonymized_code)
        et le mapping complet (original_text -> anonymized_code) incluant les entités spaCy.
        """
        replacements_map_spacy, mapping_dict_spacy = self.session.generate_replacements(
            unique_spacy_entities, replacement_rules=self.replacement_rules_spacy_config
        )

        # Journaliser les remplacements spaCy
        for original, code in mapping_dict_spacy.items():
            label = next(
                (lbl for txt, lbl in unique_spacy_entities if txt == original),
                "UNKNOWN_SPACY_LABEL",
            )
            n_repl_spacy_in_block = 0
            # Compter les occurrences dans tous les blocs pour l'audit log
            for block_entities in entities_per_block_with_offsets:
                for ent_text_offset, ent_label_offset, _, _ in block_entities:
                    if ent_text_offset == original and ent_label_offset == label:
                        n_repl_spacy_in_block += 1

            if n_repl_spacy_in_block > 0:
                self.audit_logger.log(
                    original, code, f"spacy_{label}", n_repl_spacy_in_block
                )

        return replacements_map_spacy, mapping_dict_spacy
