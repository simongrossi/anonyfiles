import pytest

pytest.importorskip("typer")
from typer.testing import CliRunner  # noqa: E402
from pathlib import Path  # noqa: E402
from types import SimpleNamespace  # noqa: E402
from unittest.mock import patch  # noqa: E402
import zipfile  # noqa: E402
import json  # noqa: E402

from anonyfiles_cli.main import app  # noqa: E402
from anonyfiles_core.anonymizer import spacy_engine  # noqa: E402
from anonyfiles_cli.managers.config_manager import ConfigManager  # noqa: E402


class DummyRuler:
    def add_patterns(self, patterns):
        self.patterns = patterns


class DummyModel:
    def __init__(self):
        self.pipe_names = ["ner"]

    def add_pipe(self, name, before=None):
        self.pipe_names.insert(0, name)
        return DummyRuler()

    def __call__(self, text):
        return SimpleNamespace(ents=[])


def _fake_spacy(load):
    """Faux module ``spacy`` complet (``util.is_package`` + ``load``)."""
    def wrapped_load(name, *args, **kwargs):
        return load(name)
    return SimpleNamespace(
        util=SimpleNamespace(is_package=lambda name: True),
        load=wrapped_load,
    )


def test_cli_anonymize_dry_run(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("Jean Dupont à Paris", encoding="utf-8")
    with patch.object(spacy_engine, "spacy", _fake_spacy(lambda name: DummyModel())):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "anonymize",
                "process",
                str(sample),
                "--config",
                "anonyfiles_core/config/config.yaml",
                "--dry-run",
            ],
        )
    assert result.exit_code == 0
    assert "Anonymisation du fichier" in result.output


def test_cli_anonymize_bundle(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("Jean Dupont à Paris", encoding="utf-8")
    out_file = tmp_path / "out.txt"
    map_file = tmp_path / "map.csv"
    log_file = tmp_path / "log.csv"
    bundle = tmp_path / "bundle.zip"
    with patch.object(spacy_engine, "spacy", _fake_spacy(lambda name: DummyModel())):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "anonymize",
                "process",
                str(sample),
                "--config",
                "anonyfiles_core/config/config.yaml",
                "--output",
                str(out_file),
                "--mapping-output",
                str(map_file),
                "--log-entities",
                str(log_file),
                "--bundle",
                str(bundle),
                "--force",
            ],
        )
    assert result.exit_code == 0
    assert bundle.exists()
    with zipfile.ZipFile(bundle) as zf:
        names = zf.namelist()
        assert out_file.name in names
        assert map_file.name in names
        assert log_file.name not in names
        assert "audit.json" in names


def test_cli_validate_config(tmp_path):
    cfg = tmp_path / "conf.yaml"
    cfg.write_text("spacy_model: fr_core_news_md\nreplacements: {}\n", encoding="utf-8")
    runner = CliRunner()
    result = runner.invoke(app, ["config", "validate-config", str(cfg)])
    assert result.exit_code == 0
    assert "Configuration valide" in result.output


def test_cli_spacy_status_json(monkeypatch):
    from anonyfiles_core.anonymizer import spacy_status

    monkeypatch.setattr(
        spacy_status,
        "get_spacy_status",
        lambda model_name: {
            "status": "ok",
            "ready": True,
            "python_version": "3.11.0",
            "spacy": {"installed": True, "version": "3.8.14"},
            "model": {
                "name": model_name,
                "installed": True,
                "version": "3.8.0",
                "spacy_version_constraint": ">=3.8.0,<3.9.0",
                "compatible": True,
            },
            "commands": {
                "install_model": f"python -m spacy download {model_name}",
                "repair_model": f"python -m spacy download {model_name}",
                "validate_models": "python -m spacy validate",
            },
            "message": "ok",
        },
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        ["utils", "spacy-status", "--model", "fr_core_news_md", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["status"] == "ok"
    assert payload["model"]["name"] == "fr_core_news_md"


def test_cli_spacy_status_fails_when_model_missing(monkeypatch):
    from anonyfiles_core.anonymizer import spacy_status

    monkeypatch.setattr(
        spacy_status,
        "get_spacy_status",
        lambda model_name: {
            "status": "missing_model",
            "ready": False,
            "python_version": "3.11.0",
            "spacy": {"installed": True, "version": "3.8.14"},
            "model": {
                "name": model_name,
                "installed": False,
                "version": None,
                "spacy_version_constraint": None,
                "compatible": None,
            },
            "commands": {
                "install_model": f"python -m spacy download {model_name}",
                "repair_model": f"python -m spacy download {model_name}",
                "validate_models": "python -m spacy validate",
            },
            "message": "missing",
        },
    )

    runner = CliRunner()
    result = runner.invoke(app, ["utils", "spacy-status", "--model", "missing_model"])

    assert result.exit_code == 3
    assert "python -m spacy download missing_model" in result.output


def test_cli_config_create_dry_run(tmp_path):
    cfg_dir = tmp_path / ".anonyfiles"
    cfg_file = cfg_dir / "config.yaml"
    with (
        patch.object(ConfigManager, "DEFAULT_USER_CONFIG_DIR", cfg_dir),
        patch.object(ConfigManager, "DEFAULT_USER_CONFIG_FILE", cfg_file),
        patch.object(ConfigManager, "create_default_user_config", return_value=None),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["config", "create", "--dry-run"])
        assert result.exit_code == 0
        assert not cfg_file.exists()
        assert "dry-run" in result.output.lower()


def test_cli_config_reset_dry_run(tmp_path):
    cfg_dir = tmp_path / ".anonyfiles"
    cfg_dir.mkdir()
    cfg_file = cfg_dir / "config.yaml"
    cfg_file.write_text("dummy", encoding="utf-8")
    with (
        patch.object(ConfigManager, "DEFAULT_USER_CONFIG_DIR", cfg_dir),
        patch.object(ConfigManager, "DEFAULT_USER_CONFIG_FILE", cfg_file),
        patch.object(ConfigManager, "create_default_user_config", return_value=None),
    ):
        runner = CliRunner()
        result = runner.invoke(app, ["config", "reset", "--dry-run"])
        assert result.exit_code == 0
        assert cfg_file.exists()
        assert "dry-run" in result.output.lower()


def test_cli_deanonymize_uses_engine(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("{{NAME}}", encoding="utf-8")
    mapping = tmp_path / "map.csv"
    mapping.write_text("anonymized,original\n{{NAME}},Jean", encoding="utf-8")

    with (
        patch("typer.rich_utils.make_panel", lambda *a, **k: "panel", create=True),
        patch(
            "anonyfiles_cli.handlers.deanonymize_handler.DeanonymizationEngine"
        ) as Engine,
    ):
        engine_inst = Engine.return_value
        engine_inst.deanonymize.return_value = {
            "status": "success",
            "restored_text": "Jean",
            "report": {"warnings_generated_during_deanonymization": []},
            "warnings": [],
        }

        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "deanonymize",
                "process",
                str(sample),
                "--mapping-csv",
                str(mapping),
                "--dry-run",
            ],
        )
        assert result.exit_code == 0
        engine_inst.deanonymize.assert_called_once()


def test_cli_verbose_outputs_debug():
    cfg = Path("anonyfiles_core/config/config.yaml")
    runner = CliRunner()
    result = runner.invoke(app, ["--verbose", "config", "validate-config", str(cfg)])
    assert result.exit_code == 0
    assert "DEBUG:root:Verbose mode enabled" in result.output


def test_cli_missing_spacy_model(tmp_path):
    sample = tmp_path / "sample.txt"
    sample.write_text("data", encoding="utf-8")

    def fail_load(name):
        raise OSError("model missing")

    spacy_engine._load_spacy_model_cached.cache_clear()
    with patch.object(spacy_engine, "spacy", _fake_spacy(fail_load)):
        runner = CliRunner()
        result = runner.invoke(
            app,
            [
                "anonymize",
                "process",
                str(sample),
                "--config",
                "anonyfiles_core/config/config.yaml",
                "--dry-run",
            ],
        )
    assert result.exit_code == 2
    assert "python -m spacy download" in result.output
