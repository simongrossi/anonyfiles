# anonyfiles_cli/anonymizer/spacy_engine.py

import spacy
import re
import logging
from functools import lru_cache
from anonyfiles_cli.exceptions import ConfigurationError

logger = logging.getLogger(__name__)

# ANCIEN: EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
# NOUVEAU: Utilise \b (word boundary) pour s'assurer que le match est une adresse email complète
# et ne capture pas la ponctuation finale si elle n'est pas structurellement une partie de l'email.
EMAIL_REGEX = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}\b"

DATE_REGEX = (
    r"\b("
    r"(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4})|"  # 12/06/1980 ou 12-06-80
    r"(?:\d{4}[/-]\d{1,2}[/-]\d{1,2})|"  # 1980-06-12
    r"(?:\d{1,2}\s+[a-zA-Zéûîôâ]+\s+\d{4})|"  # 12 juin 1980
    r"(?:le\s+\d{1,2}(?:er)?\s+[a-zA-Zéûîôâ]+\s+\d{4})"  # le 1er janvier 2020
    r")\b"
)
PHONE_REGEX = r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b"
IBAN_REGEX = r"\b[A-Z]{2}\d{2}[ ]?(?:\d[ ]?){12,26}\b"


@lru_cache(
    maxsize=2
)  # Cache jusqu'à 2 modèles spaCy (ex: 'fr_core_news_md' et 'fr_core_news_lg')
def _load_spacy_model_cached(model_name: str):
    """
    Charge un modèle spaCy et met le résultat en cache.
    Cela évite de recharger le modèle si le même est demandé plusieurs fois.
    """
    logger.info("Loading spaCy model: %s (this might be cached)...", model_name)
    try:
        if not spacy.util.is_package(model_name):
            logger.warning(
                f"Model '{model_name}' not found. Attempting to download it..."
            )
            spacy.cli.download(model_name)
        return spacy.load(model_name)
    except Exception as e:
        logger.error(f"Failed to load spaCy model '{model_name}': {e}")
        # Une dernière tentative de téléchargement si l'erreur n'était pas claire
        try:
            import spacy.cli as spacy_cli

            logger.info(f"Downloading spaCy model '{model_name}' fallback...")
            spacy_cli.download(model_name)
            return spacy.load(model_name)
        except Exception as e2:
            install_cmd = f"python -m spacy download {model_name}"
            raise ConfigurationError(
                f"Could not load spaCy model '{model_name}' after auto-download attempt. Install manualy: {install_cmd}. Error: {e2}"
            ) from e2


class SpaCyEngine:
    def __init__(self, model="fr_core_news_md"):
        # Utilise la fonction de chargement mise en cache
        self.nlp = _load_spacy_model_cached(model)
        
        # Configuration de l'EntityRuler si pas déjà présent
        if "entity_ruler" not in self.nlp.pipe_names:
            # On ajoute le ruler AVANT le NER ("ner") pour que les regex aient la priorité
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            
            patterns = [
                {"label": "EMAIL", "pattern": [{"TEXT": {"REGEX": EMAIL_REGEX}}]},
                {"label": "PHONE", "pattern": [{"TEXT": {"REGEX": PHONE_REGEX}}]},
                {"label": "IBAN", "pattern": [{"TEXT": {"REGEX": IBAN_REGEX}}]},
                # Pour DATE, on s'appuie principalement sur spaCy NER ou une règle plus complexe si besoin
                # {"label": "DATE", "pattern": [{"TEXT": {"REGEX": DATE_REGEX}}]}, 
            ]
            ruler.add_patterns(patterns)
            
            # Note: Si DATE via Regex est critique et que la Regex est compatible spaCy ("TEXT" match token unique),
            # on peut l'ajouter. Sinon, le NER s'en charge généralement bien.
            
    def detect_entities(self, text, enabled_labels=None):
        """
        Détecte les entités spaCy et par regex (via EntityRuler), selon les labels activés.
        Retourne une liste (texte, label) nettoyée.
        """
        if enabled_labels is None:
            enabled_labels = set()

        # doc contient maintenant TOUT (NER + Regex) sans conflit géré par le pipeline
        doc = self.nlp(text)
        
        # Filtrage simple
        entities = [
            (ent.text, ent.label_) 
            for ent in doc.ents 
            if ent.label_ in enabled_labels
        ]
        
        return entities

    def nlp_doc(self, text):
        """Renvoie le doc spaCy (utile pour offsets, etc.)."""
        return self.nlp(text)
