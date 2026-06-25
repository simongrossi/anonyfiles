import pytest

pytest.importorskip("httpx")
import shutil
import importlib
import sys
import time
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
        for parent_name, child_name in [
            ("anonyfiles_api", "api"),
            ("anonyfiles_api", "job_utils"),
            ("anonyfiles_api.routers", "anonymization"),
        ]:
            parent = sys.modules.get(parent_name)
            if parent is not None and hasattr(parent, child_name):
                delattr(parent, child_name)
        _importlib.invalidate_caches()
        sys.modules.setdefault(
            "spacy",
            importlib.util.module_from_spec(
                importlib.machinery.ModuleSpec("spacy", None)
            ),
        )
        from anonyfiles_api.api import app

        app.state.BASE_CONFIG = {"dummy": True}

        def fake_run_anonymization_job_sync(
            job_id,
            input_path,
            config_options,
            has_header,
            custom_rules,
            passed_base_config,
        ):
            from anonyfiles_api.job_utils import Job

            saved["job_id"] = job_id
            saved["input_path"] = input_path
            Job(job_id).set_status_as_finished_sync({"audit_log": []})

        with patch(
            "anonyfiles_api.routers.anonymization.run_anonymization_job_sync",
            side_effect=fake_run_anonymization_job_sync,
        ):
            with TestClient(app) as client:
                files = {"file": ("../secret.txt", b"data")}
                data = {
                    "config_options": "{}",
                    "file_type": "txt",
                    "has_header": "",
                    "custom_replacement_rules": "",
                }
                resp = client.post("/anonymize/", files=files, data=data)
                assert resp.status_code == 200

                deadline = time.time() + 2
                while "job_id" not in saved and time.time() < deadline:
                    time.sleep(0.05)

        job_id = saved["job_id"]
        job_dir = tmp_path / job_id
        assert (job_dir / "input.txt").is_file()
        assert saved["input_path"] == job_dir / "input.txt"
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        shutil.rmtree(tmp_path / saved.get("job_id", ""), ignore_errors=True)
