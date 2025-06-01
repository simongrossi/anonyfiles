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
        # self.faker_instance = Faker('fr_FR') # Exemple

    def _generate_code(self, label: str, index: int, options: dict = None) -> str:
        """
        Génère un code unique pour chaque type d'entité au format {{TAG_XXX}},
        en utilisant les options fournies si disponibles pour le TAG interne.
        """
        options = options or {}

        # Le 'prefix' dans les options définira maintenant le TAG interne.
        # Ex: si options={"prefix": "PERSONNE"}, et label="PER", inner_tag="PERSONNE"
        # Si pas de prefix dans les options, on prend un tag par défaut basé sur le label.
        default_inner_tags = {
            "PER": "NOM",
            "LOC": "LIEU",
            "ORG": "ENTREPRISE", # Changé pour être plus distinctif que ORG
            "EMAIL": "EMAIL",
            "DATE": "DATE",
            "MISC": "DIVERS",    # Changé pour être plus distinctif que DATA
            "PHONE": "TEL",
            "IBAN": "IBAN_ID"
            # Ajoutez d'autres labels que vous gérez fréquemment
        }
        
        inner_tag = options.get("prefix", default_inner_tags.get(label, label.upper()))
        
        padding = options.get("padding", 3)
        if not isinstance(padding, int) or padding < 0:
            padding = 3 

        # Nouveau format : {{INNERTAG_XXX}}
        return f"{{{{{inner_tag}_{str(index+1).zfill(padding)}}}}}"

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
                        # Le texte de 'redact' est maintenant directement le marqueur souhaité
                        # Ex: "{{ORGANISATION_MASQUÉE}}"
                        code = rule_options.get("text", "{{REDACTED}}") # Marqueur par défaut pour redact
                    elif rule_type == "placeholder":
                        # Le format du placeholder est maintenant directement le marqueur, potentiellement avec la valeur originale
                        # Ex: "{{LIEU:{}}}" ou "{{DATE_CONFIDENTIELLE}}"
                        format_str = rule_options.get("format", "{{{}}}".format(label.upper())) # Placeholder par défaut: "{{LABEL}}" ou "{{LABEL:valeur}}" si format_str inclut "{}"
                        try:
                            code = format_str.format(entity_text)
                        except Exception as e:
                            print(f"AVERTISSEMENT (Replacer): Erreur de formatage du placeholder pour l'entité '{entity_text}' avec le format '{format_str}': {e}. Utilisation du format simple.")
                            # Fallback si le format_str est complexe et attendu pour inclure entity_text
                            # mais que entity_text cause un souci ou si le format est juste un tag sans {}
                            if "{}" in format_str: # Si le format attendait une valeur
                                code = format_str.replace("{}", "[VALEUR_ORIGINALE_ERREUR_FORMAT]")
                            else: # Si le format est juste un tag fixe
                                code = format_str
                    elif rule_type == "codes":
                        code = self._generate_code(label, current_label_index, rule_options)
                        label_counters[label] = current_label_index + 1 
                    elif rule_type == "faker":
                        # L'implémentation de Faker devrait aussi générer des chaînes au format {{TAG:ValeurFake}}
                        # ou simplement la valeur Fake si le but n'est pas d'indiquer que c'est un remplacement.
                        # Pour l'instant, on garde un marqueur clair.
                        provider = rule_options.get("provider", label.lower()) # ex: "name", "address"
                        code = f"{{{{FAKER_{provider.upper()}}}}}" # Placeholder simple
                    else:
                        print(f"AVERTISSEMENT (Replacer): Type de règle '{rule_type}' inconnu pour label '{label}'. Utilisation de la génération de code par défaut.")
                        code = self._generate_code(label, current_label_index, rule_options) # Utilise rule_options si dispo
                        label_counters[label] = current_label_index + 1
                else: # Pas de règle spécifique ou règle malformée
                    code = self._generate_code(label, current_label_index) # Utilise les options par défaut de _generate_code
                    label_counters[label] = current_label_index + 1
                
                entity_seen[entity_text] = code

            replacements[entity_text] = code
            mapping[entity_text] = code

        return replacements, mapping