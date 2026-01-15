# anonyfiles_cli/commands/__init__.py

# Importe les objets 'app' de chaque module de commande
# Ces imports rendent les applications Typer disponibles pour le main.py
from . import anonymize  # noqa: F401
from . import deanonymize  # noqa: F401
from . import config  # noqa: F401
from . import batch  # noqa: F401
from . import utils  # noqa: F401
from . import clean_job  # noqa: F401
from . import logs  # noqa: F401
