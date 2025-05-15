# anonymizer/replacer.py
from faker import Faker
from typing import List, Tuple, Dict, Any, Optional

class ReplacementSession:
    def __init__(self, locale: str = "fr_FR"):
        self.faker = Faker(locale)
        self.person_code_map: Dict[str, str] = {}
        self.person_counter: int = 0
        self.faker_consistency_map: Dict[str, str] = {}
        # ... Ajoute d'autres maps si tu veux la cohérence sur d'autres labels

    def generate_replacements(
        self,
        entities: List[Tuple[str, str]],
        replacement_rules: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Génère un mapping de remplacements pour les entités fournies.
        Chaque instance est isolée (pas de global).
        """
        replacements: Dict[str, str] = {}

        sorted_entities = sorted(entities, key=lambda item: (item[1], item[0]))

        for text, label in sorted_entities:
            clean_text = text.strip()
            if clean_text in replacements:
                continue

            # --- Sélection de la règle
            rule = (replacement_rules or {}).get(label, {"type": "redact"})

            if rule["type"] == "codes":
                # Remplacement PER → NOMxxx
                if clean_text not in self.person_code_map:
                    self.person_counter += 1
                    prefix = rule.get("options", {}).get("prefix", "NOM")
                    padding = rule.get("options", {}).get("padding", 3)
                    code = f"{prefix}{str(self.person_counter).zfill(padding)}"
                    self.person_code_map[clean_text] = code
                replacement_text = self.person_code_map[clean_text]

            elif rule["type"] == "faker":
                if clean_text not in self.faker_consistency_map:
                    # Tu peux ici choisir le faker en fonction du label
                    if label == "PER":
                        val = self.faker.name()
                    elif label == "LOC":
                        val = self.faker.city()
                    elif label == "ORG":
                        val = self.faker.company()
                    elif label == "DATE":
                        val = self.faker.date()
                    elif label == "EMAIL":
                        val = self.faker.email()
                    else:
                        val = "[FAKER_REDACTED]"
                    self.faker_consistency_map[clean_text] = val
                replacement_text = self.faker_consistency_map[clean_text]

            elif rule["type"] == "redact":
                replacement_text = rule.get("options", {}).get("text", "[REDACTED]")

            elif rule["type"] == "placeholder":
                format_string = rule.get("options", {}).get("format", "[{}_ANONYME]")
                try:
                    replacement_text = format_string.format(label)
                except Exception:
                    replacement_text = "[INVALID_PLACEHOLDER_FORMAT]"

            else:
                replacement_text = "[REDACTED]"

            replacements[clean_text] = replacement_text

        return replacements, dict(self.person_code_map)  # copie pour ne pas exposer l’état interne

# Utilisation :
# session = ReplacementSession()
# replacements, person_map = session.generate_replacements(entities, replacement_rules)
