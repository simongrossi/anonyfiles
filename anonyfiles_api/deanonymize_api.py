# anonyfiles_api/deanonymize_api.py

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pathlib import Path
import shutil, uuid, json
import logging

from fastapi.responses import JSONResponse

# Ajout des modules internes
try:
    from anonyfiles.anonyfiles_cli.deanonymize import Deanonymizer
    from anonyfiles.anonyfiles_cli.anonymizer.file_utils import default_output, ensure_folder, timestamp
    from anonyfiles.anonyfiles_cli.anonymizer.run_logger import log_run_event
    from anonyfiles.anonyfiles_api.cli_logger import CLIUsageLogger
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "anonyfiles_cli"))
    from deanonymize import Deanonymizer
    from anonymizer.file_utils import default_output, ensure_folder, timestamp
    from anonymizer.run_logger import log_run_event
    from cli_logger import CLIUsageLogger

router = APIRouter()
JOBS_DIR = Path("jobs")
JOBS_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)

def run_deanonymization_job(
    job_id: str,
    input_path: Path,
    mapping_path: Path,
    permissive: bool,
):
    run_dir = input_path.parent
    try:
        logger.info(f"[{job_id}] Démarrage de la désanonymisation")
        deanonymizer = Deanonymizer(str(mapping_path), strict=not permissive)

        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        output_path = default_output(input_path, run_dir, append_timestamp=True).with_name(
            input_path.stem + "_deanonymise_" + timestamp() + ".txt"
        )
        report_path = run_dir / "report.json"
        audit_log_path = run_dir / "audit_log.json"
        status_path = run_dir / "status.json"

        result_text, report = deanonymizer.deanonymize_text(content, dry_run=False)

        # Écriture des fichiers
        output_path.write_text(result_text, encoding="utf-8")
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        audit_log_path.write_text(json.dumps(report.get("warnings", []), indent=2, ensure_ascii=False), encoding="utf-8")
        status_path.write_text(json.dumps({"status": "finished", "error": None}), encoding="utf-8")

        # Logging centralisé
        log_run_event(
            CLIUsageLogger,
            run_id=job_id,
            input_file=str(input_path),
            output_file=str(output_path),
            mapping_file=str(mapping_path),
            log_entities_file="",
            entities_detected=list(report.get("codes_found", [])),
            total_replacements=report.get("replaced_count", 0),
            audit_log=report.get("warnings", []),
            status="success",
            error=None
        )
        logger.info(f"[{job_id}] Désanonymisation terminée avec succès")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id}] Erreur de désanonymisation : {error_msg}", exc_info=True)
        (run_dir / "status.json").write_text(json.dumps({"status": "error", "error": error_msg}), encoding="utf-8")

        log_run_event(
            CLIUsageLogger,
            run_id=job_id,
            input_file=str(input_path),
            output_file="",
            mapping_file=str(mapping_path),
            log_entities_file="",
            entities_detected=[],
            total_replacements=0,
            audit_log=[],
            status="error",
            error=error_msg
        )


@router.post("/api/deanonymize/")
async def deanonymize_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mapping: UploadFile = File(...),
    permissive: bool = Form(False)
):
    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    ensure_folder(job_dir)

    input_path = job_dir / file.filename
    mapping_path = job_dir / mapping.filename

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    with open(mapping_path, "wb") as buffer:
        shutil.copyfileobj(mapping.file, buffer)

    (job_dir / "status.json").write_text(json.dumps({"status": "pending", "error": None}), encoding="utf-8")

    background_tasks.add_task(
        run_deanonymization_job,
        job_id=job_id,
        input_path=input_path,
        mapping_path=mapping_path,
        permissive=permissive,
    )

    return {"job_id": job_id, "status": "pending"}


@router.get("/deanonymize_status/{job_id}")
async def deanonymize_status(job_id: str):
    job_dir = JOBS_DIR / job_id
    status_file = job_dir / "status.json"
    if not status_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")

    with open(status_file, "r", encoding="utf-8") as f:
        status = json.load(f)

    if status["status"] == "finished":
        try:
            output_file = sorted(job_dir.glob("*_deanonymise_*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)[0]
            report_file = job_dir / "report.json"
            audit_file = job_dir / "audit_log.json"
            return {
                "status": "finished",
                "deanonymized_text": output_file.read_text(encoding="utf-8") if output_file.exists() else "",
                "report": json.loads(report_file.read_text(encoding="utf-8")) if report_file.exists() else {},
                "audit_log": json.loads(audit_file.read_text(encoding="utf-8")) if audit_file.exists() else [],
            }
        except Exception as e:
            return {"status": "error", "error": f"Could not retrieve files: {str(e)}"}
    else:
        return status
