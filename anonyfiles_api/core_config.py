# anonyfiles_api/core_config.py
import logging
import sys
import yaml
from pathlib import Path
from contextvars import ContextVar
from typing import Optional, Dict, Any
from pydantic import Field, BaseModel
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

# Configuration du Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("anonyfiles_api")

# ContextVar pour stocker l'ID du job courant
_job_id_ctx: ContextVar[Optional[str]] = ContextVar("job_id", default=None)
_request_context_path: ContextVar[Optional[str]] = ContextVar(
    "request_path", default=None
)
_request_context_ip: ContextVar[Optional[str]] = ContextVar("request_ip", default=None)

# --- Constantes ---
CONFIG_TEMPLATE_PATH = (
    Path(__file__).resolve().parent.parent
    / "anonyfiles_core"
    / "config"
    / "config.yaml"
)
JOBS_DIR = Path("jobs")
BASE_INPUT_STEM_FOR_JOB_FILES = "input"
DEFAULT_RATE_LIMIT = "100/minute"


# --- Modèles de Configuration ---


class ReplacementOptions(BaseModel):
    locale: Optional[str] = None
    provider: Optional[str] = None
    text: Optional[str] = None
    # Pour 'codes', pas d'options spécifiques requises mais on accepte des dicts génériques

    class Config:
        extra = "allow"  # Permettre d'autres options non explicitement définies


class EntityConfig(BaseModel):
    type: str  # ex: codes, faker, redact
    options: Optional[ReplacementOptions] = Field(default_factory=ReplacementOptions)


class AppConfig(BaseSettings):
    # Configuration principale
    spacy_model: str = Field(
        default="fr_core_news_md", description="Modèle spaCy par défaut"
    )

    # Configuration des actions de remplacement pour chaque entité
    replacements: Dict[str, EntityConfig] = Field(default_factory=dict)

    # Autres configurations globales potentielles
    cors_origins: str = Field(
        default="", description="Origines CORS autorisées (séparées par des virgules)"
    )
    debug: bool = False

    model_config = SettingsConfigDict(
        env_prefix="ANONYFILES_",  # Les vars d'env préfixées par ANONYFILES_ surchargeront
        env_nested_delimiter="__",  # Pour surcharger replacements__PER__type
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        Définit la priorité des sources de configuration.
        1. Init settings (arguments passés au constructeur)
        2. Env settings (variables d'environnement)
        3. YAML file (notre source personnalisée)
        4. Defaults
        """
        return (
            init_settings,
            env_settings,
            YamlConfigSettingsSource(CONFIG_TEMPLATE_PATH),
            # dotenv_settings, # Si on utilisait .env
            # file_secret_settings,
        )


# Source de configuration personnalisée pour YAML
class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    def __init__(self, yaml_file: Path):
        self.yaml_file = yaml_file

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        # Cette méthode n'est pas appelée directement si on return tout le dict dans __call__
        # mais est requise par l'interface abstraite ou l'implémentation de base.
        # Ici on simplifie en retournant tout le dictionnaire chargé.
        pass

    def __call__(self) -> Dict[str, Any]:
        if not self.yaml_file.is_file():
            logger.warning(
                f"Fichier de configuration YAML non trouvé : {self.yaml_file}"
            )
            return {}

        try:
            with open(self.yaml_file, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not isinstance(config_data, dict):
                logger.warning(
                    f"Le fichier {self.yaml_file} ne contient pas un dictionnaire valide."
                )
                return {}

            logger.info(f"Configuration chargée depuis {self.yaml_file}")
            return config_data
        except Exception as e:
            logger.error(f"Erreur lors du chargement de {self.yaml_file}: {e}")
            return {}


# --- Fonctions utilitaires contextuelles ---


def set_job_id(job_id: Optional[str] = None) -> None:
    _job_id_ctx.set(job_id)


def get_job_id() -> Optional[str]:
    return _job_id_ctx.get()


def set_request_context(path: str, ip: str):
    _request_context_path.set(path)
    _request_context_ip.set(ip)


def clear_request_context():
    _request_context_path.set(None)
    _request_context_ip.set(None)
