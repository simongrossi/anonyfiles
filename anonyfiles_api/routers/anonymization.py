# anonyfiles/anonyfiles_api/routers/anonymization.py

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Form,
    BackgroundTasks,
    HTTPException,
    Request,
)
from fastapi.responses import JSONResponse
from fastapi.concurrency import run_in_threadpool
from typing import Optional, Any, Dict
from pathlib import Path
import json
import uuid
import aiofiles.os as aio_os

from pydantic import ValidationError

from ..core_config import logger, set_job_id, AnonymizationOptions
from ..job_utils import Job, BASE_INPUT_STEM_FOR_JOB_FILES
from ..upload_utils import (
    UploadTooLargeError,
    safe_upload_filename,
    stream_upload_to_path,
)

from anonyfiles_core.anonymizer.run_logger import log_run_event
from anonyfiles_core.anonymizer.engine_options import (
    build_exclude_entities,
    build_processor_kwargs,
    parse_custom_replacement_rules,
)
from anonyfiles_cli.cli_logger import CLIUsageLogger
from anonyfiles_core import AnonyfilesEngine
from anonyfiles_core.anonymizer.file_utils import (
    default_output,
    default_mapping,
    default_log,
)

router = APIRouter()


def _prepare_engine_options(
    config_options: dict, custom_rules: Optional[list]
) -> Dict[str, Any]:
    """Create options for :class:`AnonyfilesEngine` from the request payload."""
    exclude_entities = build_exclude_entities(
        config_options, has_custom_rules=bool(custom_rules)
    )
    return {
        "exclude_entities_cli": exclude_entities,
        "custom_replacement_rules": custom_rules,
    }


def _prepare_processor_kwargs(
    input_path: Path, has_header: Optional[bool]
) -> Dict[str, Any]:
    """Build keyword arguments for the engine processor."""
    return build_processor_kwargs(input_path, has_header=has_header)


def _execute_engine_anonymization(
    engine: AnonyfilesEngine,
    input_path: Path,
    output_path: Path,
    log_entities_path: Path,
    mapping_output_path: Path,
    processor_kwargs: dict,
) -> Dict[str, Any]:
    """Run the anonymization engine synchronously."""
    logger.info(
        f"Tâche {input_path.parent.name}: Exécution du moteur AnonyfilesEngine."
    )
    return engine.anonymize(
        input_path=input_path,
        output_path=output_path,
        entities=None,
        dry_run=False,
        log_entities_path=log_entities_path,
        mapping_output_path=mapping_output_path,
        **processor_kwargs,
    )


async def _execute_engine_anonymization_async(
    engine: AnonyfilesEngine,
    input_path: Path,
    output_path: Path,
    log_entities_path: Path,
    mapping_output_path: Path,
    processor_kwargs: dict,
) -> Dict[str, Any]:
    """Run the anonymization engine asynchronously."""
    logger.info(
        f"Tâche {input_path.parent.name}: Exécution du moteur AnonyfilesEngine (async)."
    )
    return await engine.anonymize_async(
        input_path=input_path,
        output_path=output_path,
        entities=None,
        dry_run=False,
        log_entities_path=log_entities_path,
        mapping_output_path=mapping_output_path,
        **processor_kwargs,
    )


def _process_engine_result(
    current_job: Job,
    engine_result: Dict[str, Any],
    input_path: Path,
    output_path: Path,
    mapping_output_path: Path,
    log_entities_path: Path,
) -> None:
    """Persist engine results and log the final status.

    Args:
        current_job: Job instance being processed.
        engine_result: Result dictionary returned by the engine.
        input_path: Path of the original uploaded file.
        output_path: Path to the anonymized output file.
        mapping_output_path: Path to the mapping CSV file.
        log_entities_path: Path to the entity log file.
    """

    engine_status_reported = engine_result.get("status")
    engine_status_reported = engine_result.get("status")
    engine_error_message = engine_result.get("error")

    final_status_for_log_event: str
    final_error_for_log_event: Optional[str] = None

    if engine_status_reported == "success":
        write_ok = current_job.set_status_as_finished_sync(engine_result)
        final_status_for_log_event = "success" if write_ok else "error"
        if not write_ok:
            final_error_for_log_event = f"Tâche {current_job.job_id}: Échec de l'écriture du statut 'finished'/journal d'audit après l'exécution réussie du moteur."
    else:
        error_msg_to_set = (
            engine_error_message
            or f"Erreur moteur ou statut inattendu: {engine_status_reported}"
        )
        current_job.set_status_as_error_sync(error_msg_to_set)
        final_status_for_log_event = "error"
        final_error_for_log_event = error_msg_to_set

    logger.info(
        f"Tâche {current_job.job_id}: Moteur terminé. Statut pour journal d'événement: {final_status_for_log_event}, Erreur pour journal d'événement: {final_error_for_log_event}"
    )

    log_run_event(
        logger=CLIUsageLogger,
        run_id=current_job.job_id,
        input_file=str(input_path),
        output_file=str(output_path),
        mapping_file=str(mapping_output_path),
        log_entities_file=str(log_entities_path),
        entities_detected=engine_result.get("entities_detected", []),
        total_replacements=engine_result.get("total_replacements", 0),
        audit_log=engine_result.get("audit_log", []),
        status=final_status_for_log_event,
        error=final_error_for_log_event,
    )


def _handle_job_error(
    current_job: Job,
    e: Exception,
    error_context: str,
    input_path: Path,
    output_path: Optional[Path] = None,
    mapping_output_path: Optional[Path] = None,
    log_entities_path: Optional[Path] = None,
) -> None:
    """Log an error and update the job status accordingly.

    Args:
        current_job: Job instance concerned by the error.
        e: The exception that was raised.
        error_context: Contextual information about where the error happened.
        input_path: Path to the original input file.
        output_path: Optional path to the produced output file.
        mapping_output_path: Optional path to the mapping CSV.
        log_entities_path: Optional path to the entity log file.
    """

    logger.error(f"Tâche {current_job.job_id}: {error_context} - {e}", exc_info=True)

    if isinstance(e, FileNotFoundError):
        error_message = f"Fichier non trouvé: {getattr(e, 'filename', 'N/A')}"
    elif isinstance(e, PermissionError):
        error_message = f"Erreur de permission: {getattr(e, 'strerror', 'N/A')} sur {getattr(e, 'filename', 'N/A')}"
    else:
        error_message = f"Erreur inattendue pendant {error_context}: {str(e)}"

    current_job.set_status_as_error_sync(error_message)

    log_run_event(
        logger=CLIUsageLogger,
        run_id=current_job.job_id,
        input_file=str(input_path),
        output_file=str(output_path) if output_path else "",
        mapping_file=str(mapping_output_path) if mapping_output_path else "",
        log_entities_file=str(log_entities_path) if log_entities_path else "",
        entities_detected=[],
        total_replacements=0,
        audit_log=[
            {
                "error_context": error_context,
                "original_exception": str(e),
                "reported_error": error_message,
            }
        ],
        status="error",
        error=error_message,
    )


def run_anonymization_job_sync(
    job_id: str,
    input_path: Path,
    config_options: dict,
    has_header: Optional[bool],
    custom_rules: Optional[list],
    passed_base_config: Dict[str, Any],
):
    """Execute an anonymization job in a background thread.

    Args:
        job_id: Identifier for the job directory.
        input_path: Path to the uploaded file.
        config_options: Parsed anonymization options.
        has_header: Optional CSV header flag.
        custom_rules: Optional list of user provided replacement rules.
        passed_base_config: Base configuration copied from application state.
    """

    set_job_id(job_id)
    current_job = Job(job_id)
    output_path: Optional[Path] = None
    mapping_output_path: Optional[Path] = None
    log_entities_path: Optional[Path] = None

    if passed_base_config is None or not passed_base_config:
        logger.error(
            f"Tâche {job_id}: La configuration de base (passed_base_config) est None ou vide pour la tâche de fond."
        )
        try:
            raise RuntimeError(
                "Configuration de base (passed_base_config) non fournie ou vide à la tâche de fond."
            )
        except RuntimeError as e_conf:
            _handle_job_error(
                current_job,
                e_conf,
                "Erreur configuration de base (tâche de fond)",
                input_path,
            )
        return

    try:
        logger.info(
            f"Tâche {job_id}: Démarrage pour {input_path.name}. Règles perso: {custom_rules}. Utilisation de la config de base passée."
        )
        engine_opts = _prepare_engine_options(config_options, custom_rules)
        processor_kwargs = _prepare_processor_kwargs(input_path, has_header)

        output_path = default_output(
            input_path, current_job.job_dir, append_timestamp=True
        )
        log_entities_path = default_log(input_path, current_job.job_dir)
        mapping_output_path = default_mapping(input_path, current_job.job_dir)

        engine = AnonyfilesEngine(config=passed_base_config, **engine_opts)
        engine_result = _execute_engine_anonymization(
            engine,
            input_path,
            output_path,
            log_entities_path,
            mapping_output_path,
            processor_kwargs,
        )

        _process_engine_result(
            current_job,
            engine_result,
            input_path,
            output_path,
            mapping_output_path,
            log_entities_path,
        )
    except FileNotFoundError as e_fnf:
        _handle_job_error(
            current_job,
            e_fnf,
            "Fichier non trouvé",
            input_path,
            output_path,
            mapping_output_path,
            log_entities_path,
        )
    except PermissionError as e_perm:
        _handle_job_error(
            current_job,
            e_perm,
            "Erreur de permission",
            input_path,
            output_path,
            mapping_output_path,
            log_entities_path,
        )
    except Exception as e:
        _handle_job_error(
            current_job,
            e,
            "Erreur inattendue pendant l'exécution de la tâche",
            input_path,
            output_path,
            mapping_output_path,
            log_entities_path,
        )
    finally:
        logger.info(
            f"Tâche {job_id}: Traitement de run_anonymization_job_sync terminé."
        )
        set_job_id(None)


@router.post("/anonymize/", tags=["Anonymisation"])
async def anonymize_file_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    config_options: str = Form(...),
    # MODIFICATION CLÉ ICI :
    # Conserver Form(None) pour l'API, mais ajouter plus de robustesse au parsing JSON.
    custom_replacement_rules: Optional[str] = Form(None),
    file_type: Optional[str] = Form(None),
    has_header: Optional[str] = Form(None),
):
    """Handle file upload and start an anonymization job.

    Args:
        request: Current request object used to access application state.
        background_tasks: FastAPI background task manager.
        file: Uploaded file to anonymize.
        config_options: JSON string with anonymization options.
        custom_replacement_rules: Optional JSON list of replacement rules.
        file_type: Optional hint about the uploaded file type.
        has_header: Optional flag indicating if a CSV has a header row.

    Returns:
        A dictionary containing the job ID and its initial status.
    """

    job_id = str(uuid.uuid4())
    set_job_id(job_id)
    current_job = Job(job_id)

    logger.info(
        f"Requête d'anonymisation tâche: {job_id}, fichier: {file.filename}, type: {file_type}, header: {has_header}"
    )

    await aio_os.makedirs(current_job.job_dir, exist_ok=True)

    safe_name = safe_upload_filename(
        file.filename,
        fallback_stem=BASE_INPUT_STEM_FOR_JOB_FILES,
        fallback_suffix=".tmp",
    )
    file_extension = Path(safe_name).suffix or ".tmp"
    input_filename_for_job = f"{BASE_INPUT_STEM_FOR_JOB_FILES}{file_extension}"
    input_path_for_job = current_job.job_dir / input_filename_for_job

    max_upload_bytes: Optional[int] = None
    settings = getattr(request.app.state, "settings", None)
    if settings is not None and getattr(settings, "max_upload_size_mb", None):
        max_upload_bytes = int(settings.max_upload_size_mb) * 1024 * 1024

    try:
        await stream_upload_to_path(
            file, input_path_for_job, max_bytes=max_upload_bytes
        )
        logger.info(
            f"Tâche {job_id}: Fichier '{input_filename_for_job}' (orig: {file.filename}) téléversé."
        )
    except UploadTooLargeError as e_size:
        logger.warning(
            f"Tâche {job_id}: Upload refusé (taille > {e_size.max_bytes} octets)."
        )
        await current_job.set_status_as_error_async(
            f"Fichier trop volumineux: limite de {e_size.max_bytes} octets dépassée."
        )
        raise HTTPException(
            status_code=413,
            detail=f"Fichier trop volumineux (limite: {e_size.max_bytes} octets).",
        )
    except OSError as e_upload:
        logger.error(
            f"Tâche {job_id}: Erreur de téléversement '{input_filename_for_job}': {e_upload}",
            exc_info=True,
        )
        await current_job.set_status_as_error_async(
            f"Échec de la sauvegarde du fichier téléversé: {str(e_upload)}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Impossible de sauvegarder le fichier téléversé pour la tâche {job_id}.",
        )
    finally:
        await file.close()

    if not await current_job.set_initial_status_async():
        logger.error(
            f"Tâche {job_id}: Échec de l'écriture du statut initial 'pending'."
        )

    try:
        config_opts_raw = json.loads(config_options)
    except json.JSONDecodeError as e_json_conf:
        error_msg = f"JSON invalide pour config_options: {str(e_json_conf)}"
        logger.error(f"Tâche {job_id}: {error_msg}", exc_info=True)
        await current_job.set_status_as_error_async(
            error_msg + " Échec du parsing des options de configuration."
        )
        raise HTTPException(status_code=400, detail=error_msg)

    if not isinstance(config_opts_raw, dict):
        error_msg = "config_options doit être un objet JSON."
        logger.error(f"Tâche {job_id}: {error_msg}")
        await current_job.set_status_as_error_async(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    try:
        validated_options = AnonymizationOptions.model_validate(config_opts_raw)
    except ValidationError as e_schema:
        error_msg = (
            "config_options contient des champs invalides ou inconnus: "
            f"{e_schema.errors()}"
        )
        logger.error(f"Tâche {job_id}: {error_msg}")
        await current_job.set_status_as_error_async(error_msg)
        raise HTTPException(status_code=400, detail=error_msg)

    config_opts_dict = validated_options.model_dump()

    try:
        custom_rules_list = parse_custom_replacement_rules(custom_replacement_rules)
    except ValueError as e_rules:
        # strict=False par défaut donc cette branche ne devrait pas être prise,
        # mais on reste défensif si le helper évolue.
        logger.warning(
            f"Tâche {job_id}: règles personnalisées ignorées: {e_rules}"
        )
        custom_rules_list = []
    if custom_replacement_rules and custom_replacement_rules.strip() and not custom_rules_list:
        logger.warning(
            f"Tâche {job_id}: custom_replacement_rules fournies mais non parsables; ignorées."
        )

    has_header_bool: Optional[bool] = None
    if has_header is not None:
        has_header_bool = has_header.lower() in (
            "1",
            "true",
            "yes",
            "on",
            "vrai",
            "oui",
        )

    current_base_config_for_task = None
    if hasattr(request.app.state, "BASE_CONFIG"):
        current_base_config_for_task = request.app.state.BASE_CONFIG

    if current_base_config_for_task is None or not current_base_config_for_task:
        error_msg = "Erreur critique: La configuration de base du serveur (app.state.BASE_CONFIG) n'est pas chargée ou est vide."
        logger.error(f"Tâche {job_id}: {error_msg}")
        await current_job.set_status_as_error_async(error_msg)
        raise HTTPException(
            status_code=500,
            detail="Erreur serveur: Configuration de base non disponible pour traiter la requête.",
        )

    background_tasks.add_task(
        run_anonymization_job_sync,
        job_id=job_id,
        input_path=input_path_for_job,
        config_options=config_opts_dict,
        has_header=has_header_bool,
        custom_rules=custom_rules_list,  # <<< C'est ici que la liste parsée est passée
        passed_base_config=current_base_config_for_task.copy(),
    )
    logger.info(f"Tâche {job_id}: Tâche de fond ajoutée pour {input_path_for_job}.")

    return {"job_id": job_id, "status": "pending"}


@router.get("/anonymize_status/{job_id}", tags=["Anonymisation"])
async def anonymize_status_endpoint(job_id: uuid.UUID):
    """Return the status and, when finished, the result files for a job.

    Args:
        job_id: Identifier of the job to query.

    Returns:
        A JSON payload describing the current status and optionally the
        anonymization results.
    """
    job_id_str = str(job_id)
    set_job_id(job_id_str)
    current_job = Job(job_id_str)
    logger.info(f"Demande de statut pour la tâche: {job_id_str}")

    if not await current_job.check_exists_async(check_status_file=True):
        logger.warning(
            f"Statut tâche {job_id_str}: Fichier status.json ou répertoire de tâche non trouvé."
        )
        raise HTTPException(
            status_code=404, detail="Tâche non trouvée ou fichier de statut manquant."
        )

    current_status = await current_job.get_status_async()
    if current_status is None:
        raise HTTPException(
            status_code=500,
            detail="Impossible de récupérer le fichier de statut de la tâche ou il est corrompu.",
        )

    logger.info(
        f"Statut tâche {job_id_str} lu depuis status.json: {current_status.get('status')}"
    )

    if current_status.get("status") == "error":
        return JSONResponse(content=current_status)

    if current_status.get("status") == "pending":
        return JSONResponse(content=current_status)

    if current_status.get("status") == "finished":
        response_payload: Dict[str, Any] = {"status": "finished"}
        if "error" in current_status and current_status["error"] is not None:
            response_payload["error"] = current_status["error"]

        response_payload["anonymized_text"] = ""
        response_payload["mapping_csv"] = ""
        response_payload["log_csv"] = ""
        response_payload["audit_log"] = []

        error_details: Dict[str, str] = {}

        try:
            output_file_path = await run_in_threadpool(
                current_job.get_file_path_sync, "output"
            )
            mapping_file_path = await run_in_threadpool(
                current_job.get_file_path_sync, "mapping"
            )
            log_entities_file_path = await run_in_threadpool(
                current_job.get_file_path_sync, "log_entities"
            )
            audit_log_file_path = await run_in_threadpool(
                current_job.get_file_path_sync, "audit_log"
            )
        except Exception as e_find:
            logger.error(
                f"Tâche {job_id_str}: Erreur d'obtention des chemins de fichiers: {e_find}",
                exc_info=True,
            )
            response_payload["status"] = "error"
            response_payload["error"] = (
                "Erreur de résolution des chemins des fichiers de résultats pour une tâche 'finished'."
            )
            return JSONResponse(content=response_payload)

        if output_file_path:
            content = await current_job.read_file_content_async(output_file_path)
            if content is not None:
                response_payload["anonymized_text"] = content
            else:
                error_details["reading_output_file"] = (
                    f"Impossible de lire le fichier de sortie: {output_file_path.name}"
                )
        else:
            error_details["finding_output_file"] = (
                "Fichier de sortie anonymisé non trouvé."
            )

        if mapping_file_path:
            content = await current_job.read_file_content_async(mapping_file_path)
            if content is not None:
                response_payload["mapping_csv"] = content
            else:
                error_details["reading_mapping_file"] = (
                    f"Impossible de lire le fichier de mapping: {mapping_file_path.name}"
                )

        if log_entities_file_path:
            content = await current_job.read_file_content_async(log_entities_file_path)
            if content is not None:
                response_payload["log_csv"] = content
            else:
                error_details["reading_log_file"] = (
                    f"Impossible de lire le fichier log_entities: {log_entities_file_path.name}"
                )

        if audit_log_file_path:
            content = await current_job.read_file_content_async(audit_log_file_path)
            if content is not None:
                try:
                    response_payload["audit_log"] = json.loads(content)
                except json.JSONDecodeError:
                    error_details["parsing_audit_log"] = (
                        "Impossible de parser audit_log.json."
                    )
            else:
                error_details["reading_audit_log"] = (
                    "Impossible de lire audit_log.json."
                )
        elif not audit_log_file_path:
            error_details["finding_audit_log"] = (
                "Fichier journal d'audit (audit_log.json) non trouvé."
            )

        if error_details:
            response_payload.setdefault("error_details", {}).update(error_details)
            if (
                "reading_output_file" in error_details
                or "finding_output_file" in error_details
            ) and not response_payload.get("error"):
                response_payload["error"] = (
                    "Échec de la récupération d'un ou plusieurs fichiers de résultats critiques."
                )

        return JSONResponse(content=response_payload)

    logger.warning(
        f"Tâche {job_id_str}: Statut inattendu '{current_status.get('status')}' trouvé dans status.json."
    )
    return JSONResponse(content=current_status)
