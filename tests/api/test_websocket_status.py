import time
import threading
import importlib
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import anonyfiles_api.core_config as core_config
from anonyfiles_api.job_utils import Job


def test_websocket_reports_status_progress(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    threads = []
    try:
        sys.modules.setdefault(
            "spacy",
            importlib.util.module_from_spec(importlib.machinery.ModuleSpec("spacy", None)),
        )
        dummy_mod = importlib.util.module_from_spec(importlib.machinery.ModuleSpec("docx", None))
        dummy_mod.Document = object
        sys.modules.setdefault("docx", dummy_mod)
        for missing in ["pandas", "fitz"]:
            sys.modules.setdefault(
                missing,
                importlib.util.module_from_spec(importlib.machinery.ModuleSpec(missing, None)),
            )
        from anonyfiles_api.api import app
        app.state.BASE_CONFIG = {"dummy": True}

        def fake_run_anonymization_job_sync(job_id, input_path, config_options, has_header, custom_rules, passed_base_config):
            def worker():
                time.sleep(1.5)
                Job(job_id).set_status_as_finished_sync({"audit_log": []})
            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        with patch(
            "anonyfiles_api.routers.anonymization.run_anonymization_job_sync",
            side_effect=fake_run_anonymization_job_sync,
        ):
            client = TestClient(app)
            files = {"file": ("input.txt", b"data")}
            data = {"config_options": "{}", "file_type": "txt", "has_header": "", "custom_replacement_rules": ""}
            resp = client.post("/anonymize/", files=files, data=data)
            assert resp.status_code == 200
            job_id = resp.json()["job_id"]

            with client.websocket_connect(f"/ws/{job_id}") as ws:
                first = ws.receive_json()
                second = ws.receive_json()
                assert first["status"] == "pending"
                assert second["status"] in {"finished", "error"}
                ws.close()
                with pytest.raises(WebSocketDisconnect):
                    ws.receive_json()
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        for t in threads:
            t.join()
