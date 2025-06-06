# anonyfiles_cli/managers/config_manager.py

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from ..exceptions import ConfigurationError
from .validation_manager import ValidationManager
from ..utils.default_paths import get_default_output_dir

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    Gère le chargement et la fusion des configurations de l'application.
    Priorité: CLI-fournie > Utilisateur (~/.anonyfiles/config.yaml) > Par défaut de l'application.
    """
    DEFAULT_USER_CONFIG_DIR = Path.home() / ".anonyfiles"
    DEFAULT_USER_CONFIG_FILE = DEFAULT_USER_CONFIG_DIR / "config.yaml"
    DEFAULT_APP_CONFIG_TEMPLATE = Path(__file__).parent.parent / "config_default.yaml"


    @classmethod
    def _load_yaml_file(cls, file_path: Path) -> Dict[str, Any]:
        """Charge un fichier YAML de manière sécurisée."""
        if not file_path.is_file():
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)
                return content if isinstance(content, dict) else {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Erreur lors du parsing YAML de '{file_path}': {e}")
        except Exception as e:
            raise ConfigurationError(f"Erreur lors de la lecture de '{file_path}': {e}")

    @classmethod
    def get_user_config(cls) -> Dict[str, Any]:
        """Charge la configuration spécifique à l'utilisateur."""
        try:
            return cls._load_yaml_file(cls.DEFAULT_USER_CONFIG_FILE)
        except ConfigurationError as e:
            logger.warning("%s", e)
            return {}

    @classmethod
    def get_effective_config(cls, cli_provided_config_path: Optional[Path]) -> Dict[str, Any]:
        """
        Charge la configuration en respectant la priorité :
        1. Fichier de configuration fourni via la CLI.
        2. Configuration utilisateur (~/.anonyfiles/config.yaml).
        3. Configuration par défaut de l'application (config_default.yaml).
        Toutes les configurations sont validées si possible.
        """
        app_default_config = {}
        try:
            app_default_config = cls._load_yaml_file(cls.DEFAULT_APP_CONFIG_TEMPLATE)
        except ConfigurationError as e:
            logger.warning(
                "Impossible de charger le template de configuration par défaut '%s': %s. L'application utilisera des valeurs par défaut minimales.",
                cls.DEFAULT_APP_CONFIG_TEMPLATE,
                e,
            )

        merged_config = app_default_config.copy()
        user_config = cls.get_user_config()
        merged_config.update(user_config)

        if cli_provided_config_path:
            cli_config = ValidationManager.load_and_validate_config(cli_provided_config_path)
            merged_config.update(cli_config)

        return merged_config

    @classmethod
    def create_default_user_config(cls) -> None:
        """
        Crée un fichier de configuration utilisateur par défaut si celui-ci n'existe pas.
        """
        cls.DEFAULT_USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not cls.DEFAULT_USER_CONFIG_FILE.exists():
            initial_user_config = {
                "default_output_dir": str(get_default_output_dir()),
                "backup_original": False,
                "compression": False,
                "spacy_model": "fr_core_news_md",
                "replacements": {
                    "PER": {"type": "codes", "options": {"prefix": "PERSON_", "padding": 3}},
                    "LOC": {"type": "faker", "options": {"locale": "fr_FR", "provider": "city"}},
                },
                "exclude_entities": []
            }
            try:
                with open(cls.DEFAULT_USER_CONFIG_FILE, "w", encoding="utf-8") as f:
                    yaml.dump(initial_user_config, f, indent=2, sort_keys=False, allow_unicode=True)
                logger.info("Configuration utilisateur par défaut créée à: %s", cls.DEFAULT_USER_CONFIG_FILE)
            except Exception as e:
                logger.error("Erreur lors de la création de la configuration utilisateur par défaut: %s", e)
