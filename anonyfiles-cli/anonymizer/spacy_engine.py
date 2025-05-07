import spacy
import re

EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'

class SpaCyEngine:
    def __init__(self, model="fr_core_news_md"):
        self.nlp = spacy.load(model)

    def detect_entities(self, text):
        doc = self.nlp(text)
        entities = [(ent.text, ent.label_) for ent in doc.ents]

        # ➕ Détection fiable des e-mails avec regex
        email_matches = re.findall(EMAIL_REGEX, text)
        for email in email_matches:
            entities.append((email, "EMAIL"))

        # ❗ Supprimer les doublons avec priorité aux vrais e-mails
        unique_entities = {}
        for entity_text, label in entities:
            # Si déjà dans le dict mais pas en EMAIL, on remplace par EMAIL
            if entity_text in unique_entities and label == "EMAIL":
                unique_entities[entity_text] = "EMAIL"
            elif entity_text not in unique_entities:
                unique_entities[entity_text] = label

        return list(unique_entities.items())
