import importlib
import importlib.metadata
import importlib.resources
import json
import platform
from typing import Any, Dict, Optional

DEFAULT_SPACY_MODEL = "fr_core_news_md"


def get_spacy_status(model_name: str = DEFAULT_SPACY_MODEL) -> Dict[str, Any]:
    """Return a fast, load-free diagnostic for spaCy and the configured model."""
    model_name = model_name or DEFAULT_SPACY_MODEL
    spacy_version = _distribution_version("spacy")
    spacy_installed = bool(spacy_version or _find_module("spacy"))

    model_installed = bool(_find_module(model_name))
    model_distribution_version = _distribution_version(model_name)
    model_meta = _read_model_meta(model_name) if model_installed else {}
    model_version = model_meta.get("version") or model_distribution_version
    spacy_constraint = model_meta.get("spacy_version")

    compatible: Optional[bool] = None
    if spacy_version and spacy_constraint:
        compatible = _is_compatible_spacy_version(spacy_version, spacy_constraint)

    status = "ok"
    ready = True
    if not spacy_installed:
        status = "missing_spacy"
        ready = False
    elif not model_installed:
        status = "missing_model"
        ready = False
    elif compatible is False:
        status = "incompatible_model"
        ready = False

    return {
        "status": status,
        "ready": ready,
        "message": _status_message(status, model_name, spacy_constraint),
        "python_version": platform.python_version(),
        "spacy": {
            "installed": spacy_installed,
            "version": spacy_version,
        },
        "model": {
            "name": model_name,
            "installed": model_installed,
            "version": model_version,
            "spacy_version_constraint": spacy_constraint,
            "compatible": compatible,
        },
        "commands": {
            "install_model": f"python -m spacy download {model_name}",
            "repair_model": f"python -m spacy download {model_name}",
            "validate_models": "python -m spacy validate",
        },
    }


def format_spacy_status_for_error(status: Dict[str, Any]) -> str:
    """Build an actionable one-line error message from ``get_spacy_status``."""
    commands = status.get("commands", {})
    model_name = status.get("model", {}).get("name", DEFAULT_SPACY_MODEL)
    install_command = commands.get(
        "install_model", f"python -m spacy download {model_name}"
    )
    validate_command = commands.get("validate_models", "python -m spacy validate")
    return (
        f"{status.get('message', 'Diagnostic spaCy non pret.')} "
        f"Reparation: {install_command}. Verification: {validate_command}."
    )


def _status_message(
    status: str, model_name: str, spacy_constraint: Optional[str]
) -> str:
    if status == "ok":
        return "spaCy et le modele configure sont disponibles."
    if status == "missing_spacy":
        return "spaCy est introuvable dans l'environnement Python courant."
    if status == "missing_model":
        return f"Le modele spaCy '{model_name}' est introuvable."
    if status == "incompatible_model":
        return (
            f"Le modele spaCy '{model_name}' est installe mais incompatible "
            f"avec la version spaCy courante (contrainte modele: {spacy_constraint})."
        )
    return "Diagnostic spaCy indetermine."


def _distribution_version(package_name: str) -> Optional[str]:
    try:
        return importlib.metadata.version(package_name)
    except importlib.metadata.PackageNotFoundError:
        return None
    except Exception:
        return None


def _find_module(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def _read_model_meta(model_name: str) -> Dict[str, Any]:
    try:
        package_root = importlib.resources.files(model_name)
    except (ImportError, ModuleNotFoundError, AttributeError, TypeError):
        return {}

    candidates = [package_root / "meta.json"]
    try:
        candidates.extend(child / "meta.json" for child in package_root.iterdir())
    except (OSError, TypeError):
        pass

    for candidate in candidates:
        try:
            if candidate.is_file():
                return json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            continue
    return {}


def _is_compatible_spacy_version(
    spacy_version: str, spacy_constraint: str
) -> Optional[bool]:
    try:
        spacy_module = importlib.import_module("spacy")
        is_compatible = getattr(
            getattr(spacy_module, "util", None), "is_compatible_version", None
        )
        if callable(is_compatible):
            result = is_compatible(spacy_version, spacy_constraint)
            if result is not None:
                return bool(result)
    except Exception:
        pass

    try:
        from packaging.specifiers import SpecifierSet
        from packaging.version import Version

        return Version(spacy_version) in SpecifierSet(spacy_constraint)
    except Exception:
        return None
