from typer.testing import CliRunner
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import importlib
import sys

sys.modules.setdefault(
    "spacy",
    importlib.util.module_from_spec(importlib.machinery.ModuleSpec("spacy", None)),
)

from anonyfiles_cli.main import app
from anonyfiles_cli.anonymizer import spacy_engine


class DummyModel:
    def __call__(self, text):
        return SimpleNamespace(ents=[])


def test_cli_anonymize_dry_run(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("Jean Dupont à Paris", encoding="utf-8")
    with patch.object(spacy_engine, "spacy", SimpleNamespace(load=lambda name: DummyModel())):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "anonymize",
                "process",
                str(sample),
                "--config",
                "anonyfiles_cli/config.yaml",
                "--dry-run",
            ],
        )
    assert result.exit_code == 0
    assert "Anonymisation du fichier" in result.output
