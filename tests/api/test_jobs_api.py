import importlib
import json
import sys
import uuid

import pytest

pytest.importorskip("httpx")
from fastapi.testclient import TestClient

import anonyfiles_api.core_config as core_config
from anonyfiles_api.job_utils import Job


def get_app():
    sys.modules.setdefault(
        "spacy",
        importlib.util.module_from_spec(importlib.machinery.ModuleSpec("spacy", None)),
    )
    from anonyfiles_api.api import app

    return app


def test_job_queue_stats_endpoint(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    try:
        app = get_app()
        with TestClient(app) as client:
            resp = client.get("/jobs/queue")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["workers"] >= 1
        assert payload["queued"] == 0
        assert payload["running"] == 0
    finally:
        core_config.JOBS_DIR = original_jobs_dir


def test_cancel_endpoint_marks_known_orphan_job_cancelled(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    try:
        app = get_app()
        job_id = str(uuid.uuid4())
        Job(job_id).set_initial_status_sync()

        with TestClient(app) as client:
            resp = client.post(f"/jobs/{job_id}/cancel")

        assert resp.status_code == 200
        payload = resp.json()
        assert payload["cancel_requested"] is True
        assert payload["status"] == "cancelled"
        assert payload["state"] == "cancelled"
    finally:
        core_config.JOBS_DIR = original_jobs_dir


def test_finished_job_status_persists_privacy_warnings(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    try:
        job_id = str(uuid.uuid4())
        job = Job(job_id)
        job.set_initial_status_sync()
        warnings = [
            {
                "kind": "EMAIL",
                "label": "Emails possibles",
                "count": 1,
                "examples": ["contact@example.com"],
                "severity": "high",
                "message": "Il reste peut-être 1 email possible dans le résultat.",
            }
        ]

        assert job.set_status_as_finished_sync(
            {
                "audit_log": [],
                "privacy_warnings": warnings,
                "privacy_warnings_count": 1,
            }
        )

        payload = json.loads(job.status_file_path.read_text(encoding="utf-8"))
        assert payload["privacy_warnings"] == warnings
        assert payload["privacy_warnings_count"] == 1
    finally:
        core_config.JOBS_DIR = original_jobs_dir
