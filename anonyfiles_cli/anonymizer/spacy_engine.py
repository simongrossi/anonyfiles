# anonyfiles/anonyfiles_cli/anonymizer/spacy_engine.py
import spacy
import re

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
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

class SpaCyEngine:
    def __init__(self, model="fr_core_news_md"):
        self.nlp = spacy.load(model)

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
                print(f">>> {label} matched via regex:", match)
                entities.append((match, label))

        # Dé-duplication avec priorité regex
        unique_entities = {}
        for entity_text, label in entities:
            if entity_text in unique_entities:
                if label in ("EMAIL", "DATE", "PHONE", "IBAN"):
                    unique_entities[entity_text] = label
            else:
                unique_entities[entity_text] = label

        return list(unique_entities.items())

    def nlp_doc(self, text):
        """Renvoie le doc spaCy (utile pour offsets, etc.)."""
        return self.nlp(text)
