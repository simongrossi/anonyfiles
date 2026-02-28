# anonyfiles_cli/anonymizer/replacer.py

import random
import string
import logging

from .format_utils import create_placeholder

logger = logging.getLogger(__name__) #
# Importer Faker si vous prévoyez de l'utiliser réellement pour le type "faker"
# from faker import Faker

class ReplacementSession:
    """
    Gère la génération des codes anonymes pour les entités détectées.
    Fournit le mapping {entity_text: code} (pas de label en clé).

    La session est STATEFUL : les appels successifs à generate_replacements()
    partagent le même espace de codes. Une entité déjà vue reçoit toujours
    le même token, même à travers plusieurs appels (batch multi-textes/multi-fichiers).

    Appeler reset() pour repartir d'une session vierge.
    """

    def __init__(self):
        # Mapping principal (entité originale → token)
        self.entity_to_code: dict = {}
        # Mapping inverse (token → entité originale), utile pour la réversibilité
        self.code_to_entity: dict = {}
        # Compteurs par label pour la numérotation séquentielle
        self._label_counters: dict = {}
        # self.faker_instance = Faker('fr_FR') # Exemple

    def reset(self):
        """Réinitialise complètement la session (nouvelle session vierge)."""
        self.entity_to_code.clear()
        self.code_to_entity.clear()
        self._label_counters.clear()

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
            # Labels spaCy standards — défauts français, surchargeable via
            # replacement_rules dans la config (clé "replacements").
            # Exemple pour des tags anglais :
            #   config["replacements"]["PER"] = {"type": "codes", "options": {"prefix": "PERSON"}}
            "PER": "NOM",
            "LOC": "LIEU",
            "ORG": "ENTREPRISE",
            "EMAIL": "EMAIL",
            "DATE": "DATE",
            "MISC": "DIVERS",
            "PHONE": "TEL",
            "IBAN": "IBAN_ID",
            # Labels sécurité / cyber (via custom_rules ou modèle NER dédié)
            "HOSTNAME": "HOST",
            "IP_ADDRESS": "IP",
            "IP_PRIVE": "IP",
            "CVE": "CVE",
            "MAC_ADDRESS": "MAC",
            "SERVICE": "SVC",
            "FIREWALL_RULE": "RULE",
            "SUBNET": "SUBNET",
            "PORT": "PORT",
            "TOKEN": "TOKEN",
        }
        
        inner_tag = options.get("prefix", default_inner_tags.get(label, label.upper()))
        
        padding = options.get("padding", 3)
        if not isinstance(padding, int) or padding < 0:
            padding = 3

        # Nouveau format : {{INNERTAG_XXX}}
        return create_placeholder(inner_tag, index, padding)

    def generate_replacements(self, unique_spacy_entities, replacement_rules=None):
        """
        Prend une liste de tuples (entity_text, label) et génère le mapping {entity_text: code}.
        Retourne: (replacements_map, mapping_dict)

        La session est stateful : entity_to_code et _label_counters persistent entre
        les appels successifs. Une entité déjà vue reçoit toujours le même token.
        Appeler reset() pour repartir d'une session vierge.
        """
        replacements = {}
        mapping = {}

        if not replacement_rules:
            replacement_rules = {}

        for entity_text, label in unique_spacy_entities:
            if entity_text in self.entity_to_code:
                # Entité déjà vue dans cette session → réutilise le token existant
                code = self.entity_to_code[entity_text]
            else:
                current_label_index = self._label_counters.get(label, 0)
                rule = replacement_rules.get(label)

                if rule and isinstance(rule, dict):
                    rule_options = rule.get("options", {})
                    rule_type = rule.get("type")

                    if rule_type == "redact":
                        code = rule_options.get("text", "{{REDACTED}}")
                    elif rule_type == "placeholder":
                        format_str = rule_options.get("format", "{{{}}}".format(label.upper()))
                        try:
                            code = format_str.format(entity_text)
                        except Exception as e:
                            logger.warning(
                                "Erreur de formatage du placeholder pour l'entité '%s' avec le format '%s': %s. Utilisation du format simple.",
                                entity_text, format_str, e,
                            )
                            if "{}" in format_str:
                                code = format_str.replace("{}", "[VALEUR_ORIGINALE_ERREUR_FORMAT]")
                            else:
                                code = format_str
                    elif rule_type == "codes":
                        code = self._generate_code(label, current_label_index, rule_options)
                        self._label_counters[label] = current_label_index + 1
                    elif rule_type == "faker":
                        provider = rule_options.get("provider", label.lower())
                        code = f"{{{{FAKER_{provider.upper()}}}}}"
                    else:
                        logger.warning(
                            "Type de règle '%s' inconnu pour label '%s'. Utilisation de la génération de code par défaut.",
                            rule_type, label,
                        )
                        code = self._generate_code(label, current_label_index, rule_options)
                        self._label_counters[label] = current_label_index + 1
                else:
                    code = self._generate_code(label, current_label_index)
                    self._label_counters[label] = current_label_index + 1

                # Enregistrement dans la session
                self.entity_to_code[entity_text] = code
                self.code_to_entity[code] = entity_text

            replacements[entity_text] = code
            mapping[entity_text] = code

        return replacements, mapping
