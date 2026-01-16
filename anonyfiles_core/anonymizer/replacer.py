# anonyfiles_cli/anonymizer/replacer.py
import logging
import hashlib
from typing import Dict, Any, Callable

from .format_utils import create_placeholder

logger = logging.getLogger(__name__)

# Registry pour stocker les generateurs
_GENERATOR_REGISTRY: Dict[str, Callable] = {}


def register_generator(rule_type: str):
    """Décorateur pour enregistrer une fonction de génération."""

    def decorator(func: Callable):
        _GENERATOR_REGISTRY[rule_type] = func
        return func

    return decorator


# --- Fonctions de génération ---


@register_generator("codes")
def generate_code_replacement(
    session: "ReplacementSession",
    label: str,
    index: int,
    options: Dict[str, Any],
    entity_text: str,
) -> str:
    """Génère un code séquentiel (ex: {{NOM_001}}). Incrémente le compteur."""
    # Le 'prefix' dans les options définira maintenant le TAG interne.
    default_inner_tags = {
        "PER": "NOM",
        "LOC": "LIEU",
        "ORG": "ENTREPRISE",
        "EMAIL": "EMAIL",
        "DATE": "DATE",
        "MISC": "DIVERS",
        "PHONE": "TEL",
        "IBAN": "IBAN_ID",
    }
    inner_tag = options.get("prefix", default_inner_tags.get(label, label.upper()))
    padding = options.get("padding", 3)
    # Incrémentation gérée par l'appelant via l'index passé
    return create_placeholder(inner_tag, index, padding)


@register_generator("redact")
def generate_redaction_replacement(
    session: "ReplacementSession",
    label: str,
    index: int,
    options: Dict[str, Any],
    entity_text: str,
) -> str:
    """
    Remplace par un texte statique masqué, rendu unique par un index.
    Ex: [NOM_MASQUÉ] -> [NOM_MASQUÉ_1]
    """
    base_text = options.get("text", "{{REDACTED}}")
    
    # Si le texte contient un placeholder de formatage {}, on l'utilise
    if "{}" in base_text:
        # On suppose que l'utilisateur veut l'index ici (base 1 ou 0 selon préférence, ici +1 pour user-friendly)
        return base_text.format(index + 1)

    # Sinon comportement legacy
    # On insère l'index avant le dernier caractère si c'est un crochet ou une accolade, sinon à la fin
    # Heuristique simple : si finit par "]" ou "}", on insère avant.
    if base_text.endswith("]") or base_text.endswith("}"):
        return f"{base_text[:-1]}_{index + 1}{base_text[-1]}"
    return f"{base_text}_{index + 1}"


@register_generator("placeholder")
def generate_placeholder_replacement(
    session: "ReplacementSession",
    label: str,
    index: int,
    options: Dict[str, Any],
    entity_text: str,
) -> str:
    """
    Remplace par un format dynamique. Ajoute un index pour l'unicité si non présent.
    """
    format_str = options.get("format", "{{{}}}".format(label.upper()))
    try:
        # Essai de formatage standard
        formatted = format_str.format(entity_text)
        # Pour garantir la bijectivité, on ajoute l'index si le format ne semble pas déjà unique (ce qui est dur à savoir)
        # Par sécurité, on ajoute l'index en suffixe du tag si ça ressemble à un tag {{TAG...}}
        if formatted.startswith("{{") and formatted.endswith("}}"):
            return f"{formatted[:-2]}_{index + 1}}}"
        return f"{formatted}_{index + 1}"
    except Exception as e:
        logger.warning(
            "Erreur format placeholder '%s' pour '%s': %s", format_str, entity_text, e
        )
        return f"{format_str}_{index + 1}"


from faker import Faker

# Cache pour éviter de recréer l'objet Faker à chaque appel
_faker_instances = {}

def get_faker(locale="fr_FR"):
    if locale not in _faker_instances:
        _faker_instances[locale] = Faker(locale)
    return _faker_instances[locale]


@register_generator("faker")
def generate_faker_replacement(
    session: "ReplacementSession",
    label: str,
    index: int,
    options: Dict[str, Any],
    entity_text: str,
) -> str:
    locale = options.get("locale", "fr_FR")
    fake = get_faker(locale)
    
    # Mapping entre label SpaCy et méthodes Faker
    provider_map = {
        "PER": fake.name,
        "LOC": fake.city, # ou fake.address selon préférence
        "ORG": fake.company,
        "EMAIL": fake.email,
        "PHONE": fake.phone_number,
        "DATE": fake.date,
        "IBAN": fake.iban,
    }
    
    # Fallback générique
    provider_func = provider_map.get(label, lambda: f"FAKE_{label}")
    
    # Pour garantir la cohérence (toujours remplacer "Jean Dupont" par le même faux nom)
    if options.get("consistent", False):
        # Utilisation d'un hash stable (MD5) pour la seed, car hash() est aléatoire par processus
        seed_int = int(hashlib.md5(entity_text.encode('utf-8')).hexdigest(), 16)
        Faker.seed(seed_int)
        result = provider_func()
        # Reset seed pour ne pas casser l'aléatoire global
        Faker.seed(None) 
        return f"{result}_{index}" # On garde l'index si besoin unicité stricte
    
    return f"{provider_func()}"


class ReplacementSession:
    """
    Gère la génération des codes anonymes pour les entités détectées via un registre extensible.
    """

    def __init__(self):
        self.entity_to_code = {}

    def generate_replacements(self, unique_spacy_entities, replacement_rules=None):
        if not replacement_rules:
            replacement_rules = {}

        replacements = {}
        mapping = {}
        # Compteurs locaux pour la génération séquentielle
        label_counters = {}

        for entity_text, label in unique_spacy_entities:
            # Réutilisation si déjà vu
            if entity_text in self.entity_to_code:
                code = self.entity_to_code[entity_text]
            else:
                current_index = label_counters.get(label, 0)

                # Récupération de la règle
                rule = replacement_rules.get(label, {})
                rule_type = rule.get("type", "codes")  # Par défaut 'codes'
                options = rule.get("options", {})

                # Sélection du générateur
                generator_func = _GENERATOR_REGISTRY.get(rule_type)
                if not generator_func:
                    logger.warning(
                        "Type de règle inconnu '%s' pour '%s'. Fallback 'codes'.",
                        rule_type,
                        label,
                    )
                    generator_func = _GENERATOR_REGISTRY["codes"]

                # Génération
                try:
                    code = generator_func(
                        self, label, current_index, options, entity_text
                    )
                except Exception as e:
                    logger.error("Erreur générateur '%s': %s", rule_type, e)
                    code = f"{{{{ERR_{label}}}}}"

                # Mise à jour des compteurs seulement si le générateur est de type 'codes'
                # (ou si on décide que l'index doit toujours avancer)
                # Ici on avance toujours l'index par simplicité et unicité potentielle
                label_counters[label] = current_index + 1

                self.entity_to_code[entity_text] = code

            replacements[entity_text] = code
            mapping[entity_text] = code

        return replacements, mapping
