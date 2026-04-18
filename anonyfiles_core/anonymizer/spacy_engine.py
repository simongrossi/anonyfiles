# anonyfiles_cli/anonymizer/spacy_engine.py

import logging
import os
import re
from functools import lru_cache

import spacy

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
# TODO: Intégrer libphonenumber pour une validation internationale plus fine
# Utilise actuellement une regex française/générique
PHONE_REGEX = r"\b(?:\+33|0|[+]\d{1,3})[1-9](?:[\s.-]?\d{2}){4}\b"
IBAN_REGEX = r"\b[A-Z]{2}\d{2}[ ]?(?:\d[ ]?){12,26}\b"


# L'auto-téléchargement est souvent inapproprié en CI ou dans un sidecar
# PyInstaller packagé : on l'autorise explicitement via une variable d'env,
# et on le désactive par défaut dès qu'un runner CI est détecté.
_AUTO_DOWNLOAD_ENV = "ANONYFILES_ALLOW_SPACY_DOWNLOAD"


def _auto_download_enabled() -> bool:
    override = os.environ.get(_AUTO_DOWNLOAD_ENV)
    if override is not None:
        return override.lower() in ("1", "true", "yes", "on")
    # Désactiver par défaut en CI pour échouer vite avec un message clair.
    return not os.environ.get("CI")


def _install_hint(model_name: str) -> str:
    return (
        f"Installez-le avec: python -m spacy download {model_name} "
        f"(ou exportez {_AUTO_DOWNLOAD_ENV}=1 pour autoriser le téléchargement automatique)."
    )


@lru_cache(
    maxsize=2
)  # Cache jusqu'à 2 modèles spaCy (ex: 'fr_core_news_md' et 'fr_core_news_lg')
def _load_spacy_model_cached(model_name: str):
    """Charge (et met en cache) un modèle spaCy.

    Stratégie :
    1. Si le paquet est installé, on le charge directement. Toute erreur de
       chargement est considérée comme une corruption/incompatibilité et remonte
       sans réessayer un téléchargement (ça masquerait la vraie cause).
    2. Si le paquet est absent, on déclenche un téléchargement *unique*,
       uniquement si l'auto-download est autorisé (voir ``_auto_download_enabled``).
    3. Tous les échecs produisent un ``ConfigurationError`` explicite avec la
       commande d'installation manuelle.
    """
    logger.info("Loading spaCy model: %s (this might be cached)...", model_name)

    if spacy.util.is_package(model_name):
        try:
            return spacy.load(model_name)
        except (OSError, ImportError, ValueError) as exc:
            # Modèle présent mais illisible (ex. ABI incompatible après upgrade
            # spaCy, fichier tronqué). Ne pas re-télécharger en boucle.
            raise ConfigurationError(
                f"Le modèle spaCy '{model_name}' est installé mais ne se charge pas: {exc}. "
                f"{_install_hint(model_name)}"
            ) from exc

    if not _auto_download_enabled():
        raise ConfigurationError(
            f"Le modèle spaCy '{model_name}' est introuvable et le téléchargement "
            f"automatique est désactivé. {_install_hint(model_name)}"
        )

    logger.warning(
        "Model '%s' not found. Attempting a single download (this may take a while)...",
        model_name,
    )
    try:
        spacy.cli.download(model_name)
    except SystemExit as exc:
        # ``spacy.cli.download`` appelle ``sys.exit`` lorsque pip échoue
        # (réseau coupé, quota disque, proxy...). Le convertir en erreur typée.
        raise ConfigurationError(
            f"Échec du téléchargement automatique du modèle spaCy '{model_name}' "
            f"(code sortie pip: {exc.code}). {_install_hint(model_name)}"
        ) from exc
    except Exception as exc:  # noqa: BLE001 - on re-type immédiatement
        raise ConfigurationError(
            f"Échec du téléchargement automatique du modèle spaCy '{model_name}': {exc}. "
            f"{_install_hint(model_name)}"
        ) from exc

    try:
        return spacy.load(model_name)
    except (OSError, ImportError, ValueError) as exc:
        raise ConfigurationError(
            f"Modèle spaCy '{model_name}' téléchargé mais impossible à charger: {exc}. "
            f"{_install_hint(model_name)}"
        ) from exc


def is_valid_date(text):
    """
    Validation simple pour filtrer les faux positifs 'DATE' détectés par NER
    (ex: '1.2', '12,50', 'Chapitre 3').
    On s'assure qu'il y a au moins un séparateur de date (/,-) ou une mention d'année/mois.
    """
    # Si ça matche notre regex stricte, c'est bon
    if re.search(DATE_REGEX, text, re.IGNORECASE):
        return True

    # Sinon, on vérifie quelques heuristiques basiques
    # Doit contenir au moins un chiffre
    if not re.search(r"\d", text):
        return False

    # Éviter les nombres à virgule ou point isolés (faux positifs fréquents)
    if re.match(r"^\d+[.,]\d+$", text.strip()):
        return False

    return True


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
        entities = []
        for ent in doc.ents:
            if ent.label_ not in enabled_labels:
                continue

            # Validation supplémentaire pour réduire les faux positifs sur les dates
            if ent.label_ == "DATE" and not is_valid_date(ent.text):
                continue

            entities.append((ent.text, ent.label_))

        return entities

    def nlp_doc(self, text):
        """Renvoie le doc spaCy (utile pour offsets, etc.)."""
        return self.nlp(text)
