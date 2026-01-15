import os
from pathlib import Path

# Fallback tomli si tomllib n'est pas dispo (Python < 3.11)
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

DEFAULTS_FILE = Path(__file__).resolve().parent.parent.parent / "default_paths.toml"
ENV_VAR = "ANONYFILES_DEFAULTS_FILE"


def _load_defaults() -> dict:
    file_path = Path(os.getenv(ENV_VAR, DEFAULTS_FILE))
    if file_path.is_file():
        try:
            with open(file_path, "rb") as f:
                data = tomllib.load(f)
            paths = data.get("paths", {})
            return {k: Path(v).expanduser() for k, v in paths.items()}
        except Exception:
            return {}
    return {}


DEFAULTS = _load_defaults()


def get_default_output_dir() -> Path:
    return DEFAULTS.get("output_dir", Path.home() / "anonyfiles_outputs")


def get_default_mapping_dir() -> Path:
    return DEFAULTS.get("mapping_dir", Path.home() / "anonyfiles_mappings")


def get_default_log_dir() -> Path:
    return DEFAULTS.get("log_dir", Path.home() / "anonyfiles_logs")
