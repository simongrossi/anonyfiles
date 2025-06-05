#anonyfiles_cli/anonymizer/file_utils.py
from pathlib import Path
from datetime import datetime
import os

def timestamp() -> str:
    """Génère un timestamp au format YYYYMMDD-HHMMSS."""
    return datetime.now().strftime("%Y%m%d-%H%M%S")

def ensure_folder(folder: Path) -> None:
    """Crée le dossier s'il n'existe pas."""
    os.makedirs(folder, exist_ok=True)

def make_run_dir(base_output_dir: Path, run_id: str) -> Path:
    """Crée un dossier de run unique dans 'runs/{timestamp}/'."""
    run_dir = base_output_dir / "runs" / run_id
    ensure_folder(run_dir)
    return run_dir

def default_output(input_file: Path, run_dir: Path, append_timestamp: bool = True) -> Path:
    """Construit le chemin du fichier de sortie anonymisé."""
    base = input_file.stem
    ext = input_file.suffix
    name = f"{base}_anonymise_{timestamp()}{ext}" if append_timestamp else f"{base}_anonymise{ext}"
    return run_dir / name

def default_mapping(input_file: Path, run_dir: Path) -> Path:
    """Construit le chemin du fichier de mapping CSV."""
    base = input_file.stem
    return run_dir / f"{base}_mapping_{timestamp()}.csv"

def default_log(input_file: Path, run_dir: Path) -> Path:
    """Construit le chemin du fichier de log des entités."""
    base = input_file.stem
    return run_dir / f"{base}_entities_{timestamp()}.csv"
