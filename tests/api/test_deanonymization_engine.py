import shutil
from unittest.mock import patch
from pathlib import Path
import sys

import importlib
import anonyfiles_api.core_config as core_config


def test_run_deanonymization_job_sync_uses_engine(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    for mod in ["anonyfiles_api.job_utils", "anonyfiles_api.routers.deanonymization"]:
        if mod in sys.modules:
            del sys.modules[mod]
    importlib.invalidate_caches()
    from anonyfiles_api.job_utils import Job
    try:
        input_file = tmp_path / "sample.txt"
        input_file.write_text("{{NAME}}", encoding="utf-8")
        map_file = tmp_path / "map.csv"
        map_file.write_text("anonymized,original\n{{NAME}},Jean", encoding="utf-8")

        job_dir = Job("job1").job_dir
        job_dir.mkdir(parents=True, exist_ok=True)

        from anonyfiles_api.routers.deanonymization import run_deanonymization_job_sync

        with patch("anonyfiles_api.routers.deanonymization.DeanonymizationEngine") as Engine:
            engine_inst = Engine.return_value
            engine_inst.deanonymize.return_value = {
                "status": "success",
                "restored_text": "Jean",
                "report": {"warnings_generated_during_deanonymization": []},
                "warnings": [],
            }
            run_deanonymization_job_sync("job1", input_file, map_file, permissive=False)
            engine_inst.deanonymize.assert_called_once_with(
                input_path=input_file,
                mapping_path=map_file,
                permissive=False,
                dry_run=False,
            )

        job_dir = Job("job1").job_dir
        assert any(job_dir.glob(f"{input_file.stem}_deanonymise_*{input_file.suffix}"))
        assert (job_dir / "report.json").is_file()
    finally:
        core_config.JOBS_DIR = original_jobs_dir
        shutil.rmtree(tmp_path / "job1", ignore_errors=True)
