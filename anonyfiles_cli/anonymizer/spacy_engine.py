# anonyfiles/anonyfiles_cli/anonymizer/spacy_engine.py
import spacy
import re
from functools import lru_cache # Importe lru_cache pour le cache intelligent

# ANCIEN: EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
# NOUVEAU: Utilise \b (word boundary) pour s'assurer que le match est une adresse email complète
# et ne capture pas la ponctuation finale si elle n'est pas structurellement une partie de l'email.
EMAIL_REGEX = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}\b'

DATE_REGEX = (
    r'\b('
    r'(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|'         # 12/06/1980 ou 12-06-80
    r'(?:\d{4}[/-]\d{1,2}[/-]\d{1,2})|'           # 1980-06-12
    r'(?:\d{1,2}\s+[a-zA-Zéûîôâ]+\s+\d{4})|'      # 12 juin 1980
    r'(?:le\s+\d{1,2}(?:er)?\s+[a-zA-Zéûîôâ]+\s+\d{4})'  # le 1er janvier 2020
    r')\b'
)
PHONE_REGEX = r'\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b'
IBAN_REGEX = r'\b[A-Z]{2}\d{2}[ ]?(?:\d[ ]?){12,26}\b'


@lru_cache(maxsize=2) # Cache jusqu'à 2 modèles spaCy (ex: 'fr_core_news_md' et 'fr_core_news_lg')
def _load_spacy_model_cached(model_name: str):
    """
    Charge un modèle spaCy et met le résultat en cache.
    Cela évite de recharger le modèle si le même est demandé plusieurs fois.
    """
    print(f"Loading spaCy model: {model_name} (this might be cached)...")
    try:
        return spacy.load(model_name)
    except Exception as e:
        raise ValueError(f"Could not load spaCy model '{model_name}': {e}. "
                         "Please ensure it's installed (e.g., python -m spacy download fr_core_news_md)")


class SpaCyEngine:
    def __init__(self, model="fr_core_news_md"):
        # Utilise la fonction de chargement mise en cache
        self.nlp = _load_spacy_model_cached(model)

    def detect_entities(self, text, enabled_labels=None):
        """
        Détecte les entités spaCy et par regex, selon les labels activés.
        Retourne une liste (texte, label) SANS doublons.
        """
        if enabled_labels is None:
            enabled_labels = set()

        doc = self.nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents if ent.label_ in enabled_labels]

        regex_sources = {
            "EMAIL": EMAIL_REGEX,
            "DATE": DATE_REGEX,
            "PHONE": PHONE_REGEX,
            "IBAN": IBAN_REGEX
        }

        for label, pattern in regex_sources.items():
            if label not in enabled_labels:
                continue
            matches = re.findall(pattern, text, re.IGNORECASE if label == "DATE" else 0)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0]
                # print(f">>> {label} matched via regex:", match) # Commenté pour réduire le bruit de log
                entities.append((match, label))

        # Dé-duplication avec priorité regex (simplifiée pour la détection)
        unique_entities = {}
        for entity_text, label in entities:
            # Si l'entité_text est déjà vue, et le nouveau label est une regex (plus spécifique), on met à jour
            # Sinon, on garde le premier label ou on l'ajoute.
            if entity_text in unique_entities:
                if label in ("EMAIL", "DATE", "PHONE", "IBAN") and unique_entities[entity_text][0] not in ("EMAIL", "DATE", "PHONE", "IBAN"):
                    unique_entities[entity_text] = (label, "regex_override")
                # else: keep existing entry or handle spaCy vs regex overlap if needed
            else:
                unique_entities[entity_text] = (label, "initial")

        return [(text, label_type) for text, (label_type, _) in unique_entities.items()]


    def nlp_doc(self, text):
        """Renvoie le doc spaCy (utile pour offsets, etc.)."""
        return self.nlp(text)