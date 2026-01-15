# config_validator.py

import yaml
from cerberus import Validator
from pathlib import Path

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
        "schema": {"type": "list", "schema": {"type": "string"}},
        "default": [],
    },
    "default_output_dir": {"type": "string", "required": False},
    "backup_original": {"type": "boolean", "required": False},
    "compression": {"type": "boolean", "required": False},
}


def validate_config(config_path: Path):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    v = Validator(SCHEMA)
    if not v.validate(config):
        errors = v.errors
        raise ValueError(f"Configuration YAML invalide : {errors}")
    return config
