# anonyfiles_cli/utils/system_utils.py

import os
import sys
import typer
from pathlib import Path

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
    elif sys.platform == "darwin":  # macOS
        typer.launch(str(file_path))
    else:  # linux
        try:
            typer.launch(str(file_path))
        except Exception:
            # Note: Si vous avez une instance de ConsoleDisplay ici, vous pouvez l'utiliser
            # pour un affichage plus stylisé. Pour l'instant, un simple print.
            print(
                f"Impossible d'ouvrir le fichier avec xdg-open. Veuillez ouvrir manuellement : {file_path}"
            )


def detect_file_encoding(file_path: Path) -> str:
    """
    Détecte l'encodage d'un fichier à l'aide de chardet si disponible.
    Retourne 'utf-8' par défaut ou si chardet n'est pas installé/échoue.
    """
    if not _has_chardet:
        # Note: Si vous avez une instance de ConsoleDisplay, vous pourriez loguer un avertissement ici.
        return "utf-8"  # Fallback si chardet n'est pas disponible

    detector = UniversalDetector()
    try:
        with open(file_path, "rb") as f:
            for line in f:
                detector.feed(line)
                if detector.done:
                    break
            detector.close()
        # Assurez-vous que le résultat est un string non vide, sinon fallback
        encoding = (
            detector.result["encoding"]
            if detector.result and detector.result["encoding"]
            else "utf-8"
        )
        return encoding
    except Exception:
        # Note: Loggez l'erreur via ConsoleDisplay si possible.
        return "utf-8"  # Fallback en cas d'erreur de lecture ou de détection
