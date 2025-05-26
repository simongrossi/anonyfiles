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

class SpaCyEngine:
    def __init__(self, model="fr_core_news_md"):
        self.nlp = spacy.load(model)

    def detect_entities(self, text):
        """
        Détecte les entités nommées avec spaCy, ajoute les e-mails/dates trouvés par regex.
        Retourne une liste (texte, label) SANS doublons (priorité EMAIL/DATE regex).
        """
        doc = self.nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # Ajout des e-mails (regex)
        email_matches = re.findall(EMAIL_REGEX, text)
        for email in email_matches:
            entities.append((email, "EMAIL"))

        # Ajout des dates (regex)
        date_matches = re.findall(DATE_REGEX, text, re.IGNORECASE)
        for date in date_matches:
            # La regex retourne un tuple à cause du ( ) global, donc on récupère la première capture
            if isinstance(date, tuple):
                date = date[0]
            entities.append((date, "DATE"))

        # Filtrer les doublons (priorité EMAIL/DATE)
        unique_entities = {}
        for entity_text, label in entities:
            if entity_text in unique_entities:
                if label in ("EMAIL", "DATE"):
                    unique_entities[entity_text] = label
            else:
                unique_entities[entity_text] = label

        return list(unique_entities.items())

    def nlp_doc(self, text):
        """Renvoie le doc spaCy (utile pour offsets etc.)."""
        return self.nlp(text)
