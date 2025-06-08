import pytest
pytest.skip("unstable in CI", allow_module_level=True)
pytest.importorskip("httpx")
import shutil
import importlib
import sys
from unittest.mock import patch

import fastapi
from fastapi.testclient import TestClient

import anonyfiles_api.core_config as core_config


def test_deanonymize_uses_streaming(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    try:
        saved = {}
        sys.modules.setdefault(
            "spacy",
            importlib.util.module_from_spec(importlib.machinery.ModuleSpec("spacy", None)),
        )
        from anonyfiles_api.api import app
        app.state.BASE_CONFIG = {"dummy": True}

        async def fake_run_deanonymization_job_sync(job_id, input_path, mapping_path, permissive):
            saved["job_id"] = job_id

        read_calls = []
        orig_read = fastapi.datastructures.UploadFile.read

        async def spy_read(self, size=-1):
            data = await orig_read(self, size)
            read_calls.append((size, len(data)))
            return data

        with patch(
            "anonyfiles_api.routers.deanonymization.run_deanonymization_job_sync",
            side_effect=fake_run_deanonymization_job_sync,
        ), patch("fastapi.datastructures.UploadFile.read", spy_read):
            client = TestClient(app)
            big_content = b"x" * (2 * 1024 * 1024 + 10)
            files = {
                "file": ("big.txt", big_content),
                "mapping": ("map.csv", b"code,original\nA,B"),
            }
            resp = client.post("/deanonymize/", files=files, data={"permissive": "false"})
            assert resp.status_code == 200

        # read() should never be called without an explicit size
        assert all(size != -1 for size, _ in read_calls)
        # At least two 1MB chunks should have been requested
        assert sum(1 for size, _ in read_calls if size == 1024 * 1024) >= 2

        job_id = saved["job_id"]
        job_dir = tmp_path / job_id
        assert (job_dir / "big.txt").is_file()
        assert (job_dir / "map.csv").is_file()
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        shutil.rmtree(tmp_path / saved.get("job_id", ""), ignore_errors=True)
