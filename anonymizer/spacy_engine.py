import spacy

class SpaCyEngine:
    def __init__(self, lang_model="fr_core_news_md"):
        self.nlp = spacy.load(lang_model)

    def detect_entities(self, text):
        doc = self.nlp(text)
        return [(ent.text, ent.label_) for ent in doc.ents]
