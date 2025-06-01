# anonyfiles_cli/anonymizer/replacer.py

import random
import string
# Importer Faker si vous prévoyez de l'utiliser réellement pour le type "faker"
# from faker import Faker

class ReplacementSession:
    """
    Gère la génération des codes anonymes pour les entités détectées.
    Fournit le mapping {entity_text: code} (pas de label en clé).
    """

    def __init__(self):
        self.entity_to_code = {}
        self.code_to_entity = {}
        # Si vous utilisez Faker, initialisez-le ici, potentiellement avec une locale par défaut
        # self.faker_instance = Faker('fr_FR') # Exemple

    def _generate_code(self, label: str, index: int, options: dict = None) -> str:
        """
        Génère un code unique pour chaque type d'entité,
        en utilisant les options fournies si disponibles.
        """
        options = options or {} # S'assurer que options est un dict

        default_prefixes = {
            "PER": "NOM",
            "LOC": "LIEU",
            "ORG": "ORG",
            "EMAIL": "EMAIL",
            "DATE": "DATE",
            "MISC": "DATA",
        }
        
        prefix = options.get("prefix", default_prefixes.get(label, label.upper()))
        
        padding = options.get("padding", 3)
        if not isinstance(padding, int) or padding < 0:
            padding = 3 

        return f"{prefix}{str(index+1).zfill(padding)}"

    def generate_replacements(self, unique_spacy_entities, replacement_rules=None):
        """
        Prend une liste de tuples (entity_text, label) et génère le mapping {entity_text: code}.
        Retourne: (replacements_map, mapping_dict)
        """
        replacements = {}
        mapping = {}
        entity_seen = {} 
        label_counters = {} 

        if not replacement_rules:
            replacement_rules = {}

        for entity_text, label in unique_spacy_entities:
            if entity_text in entity_seen:
                code = entity_seen[entity_text]
            else:
                current_label_index = label_counters.get(label, 0)
                rule = replacement_rules.get(label)
                
                if rule and isinstance(rule, dict):
                    rule_options = rule.get("options", {}) 
                    rule_type = rule.get("type")

                    if rule_type == "redact":
                        code = rule_options.get("text", "[REDACTED]")
                    elif rule_type == "placeholder": # GESTION DU PLACEHOLDER AJOUTÉE
                        format_str = rule_options.get("format", "[{}]")
                        try:
                            code = format_str.format(entity_text)
                        except Exception as e:
                            print(f"AVERTISSEMENT (Replacer): Erreur de formatage du placeholder pour l'entité '{entity_text}' avec le format '{format_str}': {e}. Utilisation du texte original.")
                            code = entity_text 
                    elif rule_type == "codes": # UTILISATION DES OPTIONS POUR CODES
                        code = self._generate_code(label, current_label_index, rule_options)
                        label_counters[label] = current_label_index + 1 
                    elif rule_type == "faker":
                        locale = rule_options.get("locale") 
                        provider = rule_options.get("provider")
                        if provider:
                             code = f"[FAKE_{provider.upper()}]" # Placeholder simple
                        else:
                             code = f"[FAKE_{label.upper()}]"
                    else:
                        print(f"AVERTISSEMENT (Replacer): Type de règle '{rule_type}' inconnu pour label '{label}'. Utilisation de la génération de code par défaut.")
                        code = self._generate_code(label, current_label_index) 
                        label_counters[label] = current_label_index + 1
                else:
                    code = self._generate_code(label, current_label_index)
                    label_counters[label] = current_label_index + 1
                
                entity_seen[entity_text] = code

            replacements[entity_text] = code
            mapping[entity_text] = code

        return replacements, mapping