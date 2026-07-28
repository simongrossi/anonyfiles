# anonyfiles_cli/commands/__init__.py

# Importe les objets 'app' de chaque module de commande
# Ces imports rendent les applications Typer disponibles pour le main.py
from . import (
    anonymize,  # noqa: F401
    batch,  # noqa: F401
    clean_job,  # noqa: F401
    config,  # noqa: F401
    deanonymize,  # noqa: F401
    logs,  # noqa: F401
    utils,  # noqa: F401
)
