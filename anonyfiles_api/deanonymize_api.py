# anonyfiles_api/deanonymize_api.py

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import shutil, uuid, json

try:
    from anonyfiles.anonyfiles_cli.deanonymize import Deanonymizer
except ImportError:
    import sys
    sys.path.append(str(Path(__file__).parent.parent / "anonyfiles-cli"))
    from deanonymize import Deanonymizer

router = APIRouter()

TEMP_FILES_DIR = Path("anonyfiles_temp_data")

@router.post("/deanonymize/")
async def deanonymize_file(
    file: UploadFile = File(...),
    mapping: UploadFile = File(...),
    permissive: bool = Form(False)
):
    session_id = str(uuid.uuid4())
    session_dir = TEMP_FILES_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)

    try:
        input_path = session_dir / file.filename
        mapping_path = session_dir / mapping.filename

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        with open(mapping_path, "wb") as buffer:
            shutil.copyfileobj(mapping.file, buffer)

        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        deanonymizer = Deanonymizer(str(mapping_path), strict=not permissive)
        result, report_data = deanonymizer.deanonymize_text(content, dry_run=False)

        return {
            "status": "success",
            "deanonymized_text": result,
            "report": report_data
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erreur du serveur lors de la désanonymisation : {str(e)}")
    finally:
        if session_dir.exists():
            shutil.rmtree(session_dir, ignore_errors=True)
