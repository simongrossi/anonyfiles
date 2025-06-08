import shutil
import importlib
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

import anonyfiles_api.core_config as core_config


def test_anonymize_sanitizes_filenames(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    try:
        saved = {}
        import importlib as _importlib
        for mod in [
            "anonyfiles_api.api",
            "anonyfiles_api.routers.anonymization",
            "anonyfiles_api.job_utils",
        ]:
            if mod in sys.modules:
                del sys.modules[mod]
        _importlib.invalidate_caches()
        sys.modules.setdefault(
            "spacy",
            importlib.util.module_from_spec(importlib.machinery.ModuleSpec("spacy", None)),
        )
        from anonyfiles_api.api import app
        app.state.BASE_CONFIG = {"dummy": True}

        def fake_run_anonymization_job_sync(job_id, input_path, config_options, has_header, custom_rules, passed_base_config):
            saved["job_id"] = job_id
            saved["input_path"] = input_path

        with patch(
            "anonyfiles_api.routers.anonymization.run_anonymization_job_sync",
            side_effect=fake_run_anonymization_job_sync,
        ):
            client = TestClient(app)
            files = {"file": ("../secret.txt", b"data")}
            data = {"config_options": "{}", "file_type": "txt", "has_header": "", "custom_replacement_rules": ""}
            resp = client.post("/anonymize/", files=files, data=data)
            assert resp.status_code == 200

        job_id = saved["job_id"]
        job_dir = tmp_path / job_id
        assert (job_dir / "input.txt").is_file()
        assert saved["input_path"] == job_dir / "input.txt"
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        shutil.rmtree(tmp_path / saved.get("job_id", ""), ignore_errors=True)
