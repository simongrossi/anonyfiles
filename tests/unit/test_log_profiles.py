"""Tests des profils de logs et des options de config qu'ils utilisent.

Les profils (`anonyfiles_cli/log_profiles/*.yaml`) reposent sur trois choses
qui doivent rester vraies : le schéma accepte `custom_rules`/`description`,
le moteur expose `extra_labels`, et l'extension `.log` est traitée.
"""

from pathlib import Path

import pytest
import yaml

from anonyfiles_cli.managers.validation_manager import ValidationManager
from anonyfiles_core.anonymizer.engine import AnonyfilesEngine
from anonyfiles_core.anonymizer.file_processor_factory import FileProcessorFactory

PROFILES_DIR = Path(__file__).resolve().parents[2] / "anonyfiles_cli" / "log_profiles"


def _profile_paths():
    return sorted(PROFILES_DIR.glob("*.yaml"))


def test_profiles_are_present():
    names = {p.stem for p in _profile_paths()}
    assert {"apache", "generic_logs", "splunk", "tenable", "tufin"} <= names


@pytest.mark.parametrize("profile_path", _profile_paths(), ids=lambda p: p.stem)
def test_profile_passes_config_schema(profile_path):
    config = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    ValidationManager.validate_config_dict(config)


@pytest.mark.parametrize("profile_path", _profile_paths(), ids=lambda p: p.stem)
def test_profile_regexes_compile(profile_path):
    import re

    config = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    for rule in config.get("custom_rules", []):
        if rule.get("isRegex"):
            re.compile(rule["pattern"])


def test_apache_profile_anchors_every_line():
    """L'ancre ^ doit matcher chaque ligne : le fichier est traité en un bloc."""
    import re

    config = yaml.safe_load((PROFILES_DIR / "apache.yaml").read_text(encoding="utf-8"))
    pattern = re.compile(config["custom_rules"][0]["pattern"])
    text = "192.168.1.42 - - GET /a\n10.0.0.7 - - GET /b\n"
    assert len(pattern.findall(text)) == 2


def test_extra_labels_are_enabled():
    engine = AnonyfilesEngine(
        config={
            "spacy_model": "fr_core_news_md",
            "replacements": {},
            "extra_labels": ["IP_ADDRESS", "CVE"],
        }
    )
    assert {"IP_ADDRESS", "CVE"} <= engine.enabled_labels


def test_extra_labels_absent_leaves_defaults_untouched():
    engine = AnonyfilesEngine(
        config={"spacy_model": "fr_core_news_md", "replacements": {}}
    )
    assert "IP_ADDRESS" not in engine.enabled_labels


def test_log_extension_is_supported():
    assert FileProcessorFactory.is_extension_supported(".log")
