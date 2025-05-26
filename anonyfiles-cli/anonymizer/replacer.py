# anonyfiles_cli/anonymizer/replacer.py

import random
import string

class ReplacementSession:
    """
    Gère la génération des codes anonymes pour les entités détectées.
    Fournit le mapping {entity_text: code} (pas de label en clé).
    """

    def __init__(self):
        # On peut stocker ici les mappings utilisés si besoin d'un audit ou d'une désanonymisation
        self.entity_to_code = {}
        self.code_to_entity = {}

    def _generate_code(self, label: str, index: int) -> str:
        """Génère un code unique pour chaque type d'entité."""
        # Pour les personnes : NOM001, NOM002
        prefix = {
            "PER": "NOM",
            "LOC": "LIEU",
            "ORG": "ORG",
            "EMAIL": "EMAIL",
            "DATE": "DATE",
            "MISC": "DATA",
        }.get(label, label)
        return f"{prefix}{str(index+1).zfill(3)}"

    def generate_replacements(self, unique_spacy_entities, replacement_rules=None):
        """
        Prend une liste de tuples (entity_text, label) et génère le mapping {entity_text: code}.
        Retourne: (replacements_map, mapping_dict)
        """
        replacements = {}
        mapping = {}
        entity_seen = {}

        if not replacement_rules:
            replacement_rules = {}

        for idx, (entity_text, label) in enumerate(unique_spacy_entities):
            # Évite les doublons : toujours le même code pour une entité
            if entity_text in entity_seen:
                code = entity_seen[entity_text]
            else:
                # Si règle custom pour ce label dans replacement_rules
                rule = replacement_rules.get(label)
                if rule:
                    # On gère plusieurs types de remplacement
                    if isinstance(rule, dict):
                        # type: faker, codes, redact, etc.
                        t = rule.get("type")
                        if t == "redact":
                            code = rule.get("options", {}).get("text", "[REDACTED]")
                        elif t == "codes":
                            code = self._generate_code(label, idx)
                        elif t == "faker":
                            # (à personnaliser selon ton provider, etc.)
                            code = "[FAKE]"
                        else:
                            code = self._generate_code(label, idx)
                    else:
                        code = str(rule)
                else:
                    code = self._generate_code(label, idx)
                entity_seen[entity_text] = code

            replacements[entity_text] = code
            mapping[entity_text] = code  # mapping CSV utilisé pour déanon

        return replacements, mapping
