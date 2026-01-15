# anonyfiles_cli/managers/validation_manager.py

import json
import yaml
import logging  # Ajout de l'import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import typer
from cerberus import Validator

from ..exceptions import ConfigurationError, FileIOError

logger = logging.getLogger(__name__)  # Initialisation du logger

# Définition du SCHEMA de configuration (peut être importé de config_validator.py)
SCHEMA = {
    "spacy_model": {"type": "string", "required": True},
    "replacements": {
        "type": "dict",
        "required": True,
        "valuesrules": {
            "type": "dict",
            "schema": {
                "type": {
                    "type": "string",
                    "allowed": ["codes", "faker", "redact", "placeholder"],
                    "required": True,
                },
                "options": {"type": "dict", "required": False},
            },
        },
    },
    "exclude_entities": {
        "type": "list",
        "required": False,
        "schema": {"type": "string"},
        "default": [],
    },
    "default_output_dir": {"type": "string", "required": False},
    "backup_original": {"type": "boolean", "required": False},
    "compression": {"type": "boolean", "required": False},
}


class ValidationManager:
    """
    Gère toutes les validations pour les entrées, configurations et chemins de fichiers.
    """

    @staticmethod
    def load_and_validate_config(config_path: Path) -> Dict[str, Any]:
        """
        Charge et valide un fichier de configuration YAML.
        :param config_path: Chemin vers le fichier de configuration.
        :return: Le contenu du fichier de configuration validé.
        :raises ConfigurationError: Si le fichier est introuvable, mal formé ou invalide selon le schéma.
        """
        if not config_path.is_file():
            raise ConfigurationError(
                f"Le fichier de configuration '{config_path}' est introuvable."
            )

        try:
            with open(str(config_path), encoding="utf-8") as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Erreur lors du parsing du fichier YAML '{config_path}': {e}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Une erreur inattendue est survenue lors de la lecture de '{config_path}': {e}"
            )

        v = Validator(SCHEMA)
        if not v.validate(config):
            raise ConfigurationError(
                f"Configuration YAML invalide dans '{config_path}': {v.errors}"
            )

        return config

    @staticmethod
    def parse_custom_replacements(
        custom_replacements_json: Optional[str],
    ) -> List[Dict[str, Union[str, bool]]]:
        """
        Parse et valide la chaîne JSON des règles de remplacement personnalisées.
        :param custom_replacements_json: Chaîne JSON des règles.
        :return: Liste des règles parsées.
        :raises ConfigurationError: Si la chaîne JSON est invalide ou mal formée.
        """
        if not custom_replacements_json:
            return []
        try:
            parsed = json.loads(custom_replacements_json)
            if not isinstance(parsed, list):
                raise ConfigurationError(
                    f"Le format JSON des règles personnalisées est invalide: doit être une liste. Reçu: {type(parsed)}"
                )

            for i, rule in enumerate(parsed):
                if not isinstance(rule, dict):
                    raise ConfigurationError(
                        f"Règle personnalisée à l'index {i} est invalide: doit être un objet JSON. Reçu: {type(rule)}"
                    )
                if "pattern" not in rule or "replacement" not in rule:
                    raise ConfigurationError(
                        f"Règle personnalisée à l'index {i} est invalide: 'pattern' et 'replacement' sont requis. Règle: {rule}"
                    )
                if "isRegex" in rule and not isinstance(rule["isRegex"], bool):
                    raise ConfigurationError(
                        f"Règle personnalisée à l'index {i}: 'isRegex' doit être un booléen."
                    )

            return parsed
        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"JSON invalide pour les règles personnalisées: {e}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Une erreur inattendue est survenue lors du parsing des règles personnalisées: {e}"
            )

    @staticmethod
    def check_overwrite(paths_to_check: List[Path], force: bool):
        """
        Vérifie si des fichiers de sortie existent déjà et demande confirmation si --force n'est pas utilisé.
        :param paths_to_check: Liste des chemins de fichiers à vérifier.
        :param force: Si True, écrase sans confirmation.
        :raises FileIOError: Si l'utilisateur refuse d'écraser.
        """
        existing_files = [p for p in paths_to_check if p.exists()]

        if existing_files and not force:
            file_list = "\n".join([f"- {p}" for p in existing_files])
            prompt_message = (
                f"⚠️  Les fichiers de sortie suivants existent déjà :\n{file_list}\n"
                "Voulez-vous les écraser ? (y/N)"
            )
            response = typer.confirm(prompt_message)
            if not response:
                raise FileIOError(
                    "Opération annulée par l'utilisateur: fichiers de sortie existants non écrasés."
                )
            logger.info(
                "Continuant avec l'écrasement des fichiers existants."
            )  # Modifié pour utiliser logger.info
        elif existing_files and force:
            logger.warning(
                "⚠️  Les fichiers de sortie existants seront écrasés (mode --force)."
            )  # Modifié pour utiliser logger.warning

    @staticmethod
    def validate_config_dict(config: Dict[str, Any]) -> None:
        """Valide un dictionnaire de configuration selon ``SCHEMA``."""
        v = Validator(SCHEMA)
        if not v.validate(config):
            raise ConfigurationError(f"Configuration YAML invalide : {v.errors}")

    @staticmethod
    def ensure_spacy_model(model_name: str) -> None:
        """Vérifie que le modèle spaCy demandé est installé."""
        import importlib

        if importlib.util.find_spec(model_name) is None:
            raise ConfigurationError(
                f"Le modèle spaCy '{model_name}' est introuvable. "
                f"Installez-le avec 'python -m spacy download {model_name}'."
            )
