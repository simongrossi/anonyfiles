# anonyfiles_cli/utils/system_utils.py

import os
import sys
import typer
import logging # Ajout de l'import logging
from pathlib import Path
from typing import Optional  # Pour Optional dans detect_file_encoding

logger = logging.getLogger(__name__) # Initialisation du logger

# Importation conditionnelle de chardet
try:
    from chardet.universaldetector import UniversalDetector
    _has_chardet = True
except ImportError:
    _has_chardet = False

def open_file_in_editor(file_path: Path):
    """
    Ouvre un fichier dans l'éditeur de texte par défaut du système.
    Affiche un message si l'ouverture automatique échoue sur Linux.
    """
    if sys.platform == "win32":
        os.startfile(file_path)
    elif sys.platform == "darwin": # macOS
        typer.launch(str(file_path))
    else: # linux
        try:
            typer.launch(str(file_path))
        except Exception:
            # Note: Affiche un message utilisateur et journalise pour diagnostic
            typer.echo(
                f"Impossible d'ouvrir le fichier avec xdg-open. Veuillez ouvrir manuellement : {file_path}"
            )
            logger.warning("Failed to open file via xdg-open: %s", file_path) # Ajout du log de warning

def detect_file_encoding(file_path: Path) -> str:
    """
    Détecte l'encodage d'un fichier à l'aide de chardet si disponible.
    Retourne 'utf-8' par défaut ou si chardet n'est pas installé/échoue.
    """
    if not _has_chardet:
        # Note: Si vous avez une instance de ConsoleDisplay, vous pourriez loguer un avertissement ici.
        return 'utf-8' # Fallback si chardet n'est pas disponible

    detector = UniversalDetector()
    try:
        with open(file_path, 'rb') as f:
            for line in f:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
        # Assurez-vous que le résultat est un string non vide, sinon fallback
        encoding = detector.result['encoding'] if detector.result and detector.result['encoding'] else 'utf-8'
        return encoding
    except Exception as e:
        # Note: Loggez l'erreur via ConsoleDisplay si possible.
        logger.error("Erreur lors de la détection de l'encodage de %s: %s", file_path, e) # Ajout du log d'erreur
        return 'utf-8'  # Fallback en cas d'erreur de lecture ou de détection