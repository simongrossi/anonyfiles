import pytest
pytest.importorskip("typer")
from typer.testing import CliRunner
import importlib
import types
import sys

# Stub heavy dependencies used during CLI import with minimal attributes
sys.modules.setdefault("spacy", types.ModuleType("spacy"))

fake_docx = types.ModuleType("docx")
fake_docx.Document = lambda *a, **k: None
sys.modules.setdefault("docx", fake_docx)

sys.modules.setdefault("pandas", types.ModuleType("pandas"))
sys.modules.setdefault("fitz", types.ModuleType("fitz"))

from anonyfiles_cli.main import app


def test_job_list_nonexistent_directory(tmp_path):
    output_dir = tmp_path / "does_not_exist"
    runner = CliRunner()
    result = runner.invoke(app, ["job", "list", "--output-dir", str(output_dir)])
    assert result.exit_code == 0
    assert "Le r\xe9pertoire des jobs" in result.output
    assert "Traceback" not in result.output
