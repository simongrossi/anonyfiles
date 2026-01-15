from anonyfiles_cli.managers.validation_manager import ValidationManager


def test_validate_config_allows_extra_fields(tmp_path):
    cfg = {
        "spacy_model": "fr_core_news_md",
        "replacements": {},
        "default_output_dir": "/tmp",
        "backup_original": True,
        "compression": False,
    }
    # Should not raise
    ValidationManager.validate_config_dict(cfg)
