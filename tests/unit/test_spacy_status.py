from anonyfiles_core.anonymizer import spacy_status


def test_get_spacy_status_reports_missing_model(monkeypatch):
    def fake_distribution_version(package_name):
        if package_name == "spacy":
            return "3.8.14"
        return None

    def fake_find_module(module_name):
        return module_name == "spacy"

    monkeypatch.setattr(
        spacy_status, "_distribution_version", fake_distribution_version
    )
    monkeypatch.setattr(spacy_status, "_find_module", fake_find_module)

    status = spacy_status.get_spacy_status("missing_model")

    assert status["status"] == "missing_model"
    assert status["ready"] is False
    assert status["spacy"]["version"] == "3.8.14"
    assert status["model"]["installed"] is False
    assert (
        status["commands"]["install_model"] == "python -m spacy download missing_model"
    )


def test_get_spacy_status_reports_compatible_model(monkeypatch):
    def fake_distribution_version(package_name):
        versions = {
            "spacy": "3.8.14",
            "fr_core_news_md": "3.8.0",
        }
        return versions.get(package_name)

    monkeypatch.setattr(
        spacy_status, "_distribution_version", fake_distribution_version
    )
    monkeypatch.setattr(spacy_status, "_find_module", lambda _name: True)
    monkeypatch.setattr(
        spacy_status,
        "_read_model_meta",
        lambda _name: {"version": "3.8.0", "spacy_version": ">=3.8.0,<3.9.0"},
    )
    monkeypatch.setattr(
        spacy_status, "_is_compatible_spacy_version", lambda _version, _constraint: True
    )

    status = spacy_status.get_spacy_status("fr_core_news_md")

    assert status["status"] == "ok"
    assert status["ready"] is True
    assert status["model"]["version"] == "3.8.0"
    assert status["model"]["compatible"] is True


def test_format_spacy_status_for_error_is_actionable(monkeypatch):
    monkeypatch.setattr(spacy_status, "_distribution_version", lambda _name: None)
    monkeypatch.setattr(spacy_status, "_find_module", lambda _name: False)

    status = spacy_status.get_spacy_status("fr_core_news_md")
    message = spacy_status.format_spacy_status_for_error(status)

    assert "python -m spacy download fr_core_news_md" in message
    assert "python -m spacy validate" in message
