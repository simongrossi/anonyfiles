# anonyfiles_cli/commands/__init__.py

# Importe les objets 'app' de chaque module de commande
# Ces imports rendent les applications Typer disponibles pour le main.py
from . import anonymize
from . import deanonymize
from . import config
from . import batch
from . import utils
from . import clean_job
