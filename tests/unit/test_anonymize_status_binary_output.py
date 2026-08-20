import json
import uuid

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("aiofiles")
pytest.importorskip("pythonjsonlogger")
pytest.importorskip("spacy")

from anonyfiles_api import core_config
from anonyfiles_api.job_utils import JOBS_DIR as JOBS_DIR_DEFAULT
from anonyfiles_api.job_utils import Job
from anonyfiles_api.routers.anonymization import anonymize_status_endpoint

# Signature ZIP : suffisant pour que la lecture UTF-8 échoue comme sur un vrai .docx.
DOCX_LIKE_BYTES = b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00\xff\xfe\xfd"


def _prepare_job(tmp_path, monkeypatch, job_id: str) -> Job:
    core_config.JOBS_DIR = tmp_path
    monkeypatch.setattr("anonyfiles_api.job_utils.JOBS_DIR", tmp_path, raising=False)
    job = Job(job_id)
    job.job_dir.mkdir(parents=True, exist_ok=True)
    (job.job_dir / "status.json").write_text(
        json.dumps(
            {"status": "finished", "error": None, "original_filename": "cv.docx"}
        ),
        encoding="utf-8",
    )
    (job.job_dir / "audit_log.json").write_text("[]", encoding="utf-8")
    return job


async def _read_payload(job_id: str) -> dict:
    response = await anonymize_status_endpoint(uuid.UUID(job_id))
    return json.loads(response.body)


@pytest.mark.asyncio
async def test_binary_output_is_reported_not_treated_as_error(tmp_path, monkeypatch):
    """Une sortie .docx n'est pas lisible en texte, mais ce n'est pas une erreur.

    Avant le correctif, le job renvoyait anonymized_text="" avec une erreur
    générique : la GUI n'affichait alors ni résultat ni message (issue #76).
    """
    job_id = str(uuid.uuid4())
    original_jobs_dir = core_config.JOBS_DIR
    try:
        job = _prepare_job(tmp_path, monkeypatch, job_id)
        (job.job_dir / "input_anonymise_20260806.docx").write_bytes(DOCX_LIKE_BYTES)

        payload = await _read_payload(job_id)

        assert payload["status"] == "finished"
        assert payload["anonymized_text"] == ""
        assert payload["output_is_binary"] is True
        assert payload["output_file_name"] == "input_anonymise_20260806.docx"
        assert not payload.get("error")
        assert "reading_output_file" not in payload.get("error_details", {})
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        monkeypatch.setattr(
            "anonyfiles_api.job_utils.JOBS_DIR", JOBS_DIR_DEFAULT, raising=False
        )


@pytest.mark.asyncio
async def test_text_output_still_returned_inline(tmp_path, monkeypatch):
    job_id = str(uuid.uuid4())
    original_jobs_dir = core_config.JOBS_DIR
    try:
        job = _prepare_job(tmp_path, monkeypatch, job_id)
        (job.job_dir / "input_anonymise_20260806.txt").write_text(
            "Bonjour NOM_1\n", encoding="utf-8"
        )

        payload = await _read_payload(job_id)

        assert payload["anonymized_text"] == "Bonjour NOM_1\n"
        assert payload["output_is_binary"] is False
        assert payload["output_file_name"] == "input_anonymise_20260806.txt"
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        monkeypatch.setattr(
            "anonyfiles_api.job_utils.JOBS_DIR", JOBS_DIR_DEFAULT, raising=False
        )


@pytest.mark.asyncio
async def test_missing_output_file_is_still_an_error(tmp_path, monkeypatch):
    job_id = str(uuid.uuid4())
    original_jobs_dir = core_config.JOBS_DIR
    try:
        _prepare_job(tmp_path, monkeypatch, job_id)

        payload = await _read_payload(job_id)

        assert payload["output_is_binary"] is False
        assert payload["output_file_name"] == ""
        assert "finding_output_file" in payload["error_details"]
        assert payload["error"]
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        monkeypatch.setattr(
            "anonyfiles_api.job_utils.JOBS_DIR", JOBS_DIR_DEFAULT, raising=False
        )
