import time
import importlib
import sys
from unittest.mock import patch

import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient

import anonyfiles_api.core_config as core_config
from anonyfiles_api.job_utils import Job


def test_websocket_reports_status_progress(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    try:
        sys.modules.setdefault(
            "spacy",
            importlib.util.module_from_spec(
                importlib.machinery.ModuleSpec("spacy", None)
            ),
        )
        dummy_mod = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec("docx", None)
        )
        dummy_mod.Document = object
        sys.modules.setdefault("docx", dummy_mod)
        for missing in ["pandas", "fitz"]:
            sys.modules.setdefault(
                missing,
                importlib.util.module_from_spec(
                    importlib.machinery.ModuleSpec(missing, None)
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
            entity_decisions,
            passed_base_config,
        ):
            time.sleep(1.5)
            Job(job_id).set_status_as_finished_sync({"audit_log": []})

        with patch(
            "anonyfiles_api.routers.anonymization.run_anonymization_job_sync",
            side_effect=fake_run_anonymization_job_sync,
        ):
            with TestClient(app) as client:
                files = {"file": ("input.txt", b"data")}
                data = {
                    "config_options": "{}",
                    "file_type": "txt",
                    "has_header": "",
                    "custom_replacement_rules": "",
                }
                resp = client.post("/anonymize/", files=files, data=data)
                assert resp.status_code == 200
                job_id = resp.json()["job_id"]

                with client.websocket_connect(f"/ws/{job_id}") as ws:
                    payloads = [ws.receive_json()]
                    while payloads[-1]["status"] not in {
                        "finished",
                        "error",
                        "cancelled",
                        "timeout",
                    }:
                        payloads.append(ws.receive_json())
                    assert payloads[0]["status"] == "pending"
                    assert payloads[-1]["status"] in {
                        "finished",
                        "error",
                        "cancelled",
                        "timeout",
                    }
    finally:
        core_config.JOBS_DIR = original_jobs_dir
