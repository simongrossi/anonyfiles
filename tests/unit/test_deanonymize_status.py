import json

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("aiofiles")
pytest.importorskip("pythonjsonlogger")
pytest.importorskip("spacy")

from anonyfiles_api import core_config
from anonyfiles_api.job_utils import JOBS_DIR as JOBS_DIR_DEFAULT
from anonyfiles_api.job_utils import Job
from anonyfiles_api.routers.deanonymization import get_deanonymize_status


@pytest.mark.asyncio
async def test_get_deanonymize_status_uses_original_filename(tmp_path, monkeypatch):
    job_id = "job-123"
    original_jobs_dir = core_config.JOBS_DIR
    try:
        # Rediriger les répertoires de jobs vers le dossier temporaire
        core_config.JOBS_DIR = tmp_path
        monkeypatch.setattr("anonyfiles_api.job_utils.JOBS_DIR", tmp_path, raising=False)

        job = Job(job_id)
        job_dir = job.job_dir
        job_dir.mkdir(parents=True, exist_ok=True)

        # Le fichier de statut indique que la tâche est terminée pour un fichier Markdown
        status_payload = {
            "status": "finished",
            "error": None,
            "original_input_name": "rapport_final.md",
        }
        (job_dir / "status.json").write_text(json.dumps(status_payload), encoding="utf-8")

        # Le moteur écrit le fichier restauré en conservant le préfixe du fichier d'origine
        restored_content = "Ligne 1\nLigne 2\n"
        (job_dir / "rapport_final_deanonymise_20240101.md").write_text(restored_content, encoding="utf-8")

        # Un rapport minimal contenant les avertissements
        report_payload = {"warnings_generated_during_deanonymization": ["warn"]}
        (job_dir / "report.json").write_text(json.dumps(report_payload), encoding="utf-8")

        result = await get_deanonymize_status(job_id)

        assert result["status"] == "finished"
        assert result["deanonymized_text"] == restored_content
        assert result["audit_log"] == ["warn"]
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        monkeypatch.setattr("anonyfiles_api.job_utils.JOBS_DIR", JOBS_DIR_DEFAULT, raising=False)
