import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import importlib

import anonyfiles_api.core_config as core_config


def test_deanonymize_sanitizes_filenames(tmp_path):
    # Redirect JOBS_DIR to a temporary location
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    try:
        saved = {}
        # Import the API after mocking heavy dependencies like spaCy
        import sys
        sys.modules.setdefault("spacy", importlib.util.module_from_spec(importlib.machinery.ModuleSpec("spacy", None)))
        from anonyfiles_api.api import app
        def fake_run_deanonymization_job_sync(job_id, input_path, mapping_path, permissive):
            saved['job_id'] = job_id
            saved['input_path'] = input_path
            saved['mapping_path'] = mapping_path

        with patch(
            "anonyfiles_api.routers.deanonymization.run_deanonymization_job_sync",
            side_effect=fake_run_deanonymization_job_sync,
        ):
            client = TestClient(app)
            files = {
                "file": ("../secret.txt", b"data"),
                "mapping": ("../../map.csv", b"code,original\nA,B"),
            }
            resp = client.post("/deanonymize/", files=files, data={"permissive": "false"})
            assert resp.status_code == 200

        job_id = saved['job_id']
        job_dir = tmp_path / job_id
        assert (job_dir / "secret.txt").is_file()
        assert (job_dir / "map.csv").is_file()
        assert saved['input_path'] == job_dir / "secret.txt"
        assert saved['mapping_path'] == job_dir / "map.csv"
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        shutil.rmtree(tmp_path / saved.get('job_id', ''), ignore_errors=True)
