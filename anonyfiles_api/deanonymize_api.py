# anonyfiles_api/deanonymize_api.py

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pathlib import Path
import shutil, uuid, json

try:
    from anonyfiles.anonyfiles_cli.deanonymize import Deanonymizer
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "anonyfiles_cli"))
    from deanonymize import Deanonymizer

router = APIRouter()

JOBS_DIR = Path("jobs")

def run_deanonymization_job(
    job_id: str,
    input_path: Path,
    mapping_path: Path,
    permissive: bool,
):
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        deanonymizer = Deanonymizer(str(mapping_path), strict=not permissive)
        result, report_data = deanonymizer.deanonymize_text(content, dry_run=False)

        # Écrit résultat et statut
        (input_path.parent / "result.txt").write_text(result, encoding="utf-8")
        with open(input_path.parent / "report.json", "w", encoding="utf-8") as f:
            json.dump(report_data, f)
        with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
            json.dump({"status": "finished", "error": None}, f)
    except Exception as e:
        with open(input_path.parent / "status.json", "w", encoding="utf-8") as f:
            json.dump({"status": "error", "error": str(e)}, f)

@router.post("/api/deanonymize/")
async def deanonymize_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mapping: UploadFile = File(...),
    permissive: bool = Form(False)
):
    job_id = str(uuid.uuid4())
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    input_path = job_dir / file.filename
    mapping_path = job_dir / mapping.filename

    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    with open(mapping_path, "wb") as buffer:
        shutil.copyfileobj(mapping.file, buffer)
    with open(job_dir / "status.json", "w") as f:
        json.dump({"status": "pending", "error": None}, f)

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
        return {"error": "Job not found"}
    with open(status_file, "r", encoding="utf-8") as f:
        status = json.load(f)
    if status["status"] == "finished":
        result_file = job_dir / "result.txt"
        report_file = job_dir / "report.json"
        output = {
            "status": "finished",
            "deanonymized_text": result_file.read_text(encoding="utf-8") if result_file.exists() else "",
            "report": json.load(report_file) if report_file.exists() else {},
        }
        return output
    elif status["status"] == "error":
        return status
    else:
        return status
