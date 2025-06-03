# anonyfiles/anonyfiles_api/job_utils.py
from pathlib import Path
import shutil
import json
import aiofiles
from fastapi.concurrency import run_in_threadpool
from typing import Optional, Any, Dict

from .core_config import logger, JOBS_DIR, BASE_INPUT_STEM_FOR_JOB_FILES

class Job:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.job_dir = JOBS_DIR / self.job_id
        self.status_file_path = self.job_dir / "status.json"
        self.audit_log_file_path = self.job_dir / "audit_log.json"
        self.base_input_stem = BASE_INPUT_STEM_FOR_JOB_FILES

    async def check_exists_async(self, check_status_file: bool = True) -> bool:
        dir_exists = await run_in_threadpool(self.job_dir.exists)
        if not dir_exists: return False
        if check_status_file: return await run_in_threadpool(self.status_file_path.exists)
        return True

    async def get_status_async(self) -> Optional[Dict[str, Any]]:
        if not await run_in_threadpool(self.status_file_path.is_file):
            logger.warning(f"Tâche {self.job_id}: status.json non trouvé pour lecture du statut.")
            return None
        try:
            async with aiofiles.open(self.status_file_path, "r", encoding="utf-8") as f:
                content = await f.read()
            return json.loads(content)
        except Exception as e:
            logger.error(f"Tâche {self.job_id}: Impossible de lire/parser status.json - {e}", exc_info=True)
            return None

    def _find_latest_file_sync(self, glob_suffix_pattern: str) -> Optional[Path]:
        glob_pattern = f"{self.base_input_stem}{glob_suffix_pattern}"
        logger.debug(f"Tâche {self.job_id}: Recherche fichier {self.job_dir} motif: {glob_pattern}")
        candidates = sorted(
            [p for p in self.job_dir.glob(glob_pattern) if p.is_file()],
            key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates: return candidates[0]
        return None

    def get_file_path_sync(self, file_key: str) -> Optional[Path]:
        if file_key == "output": return self._find_latest_file_sync("_anonymise_*")
        elif file_key == "mapping": return self._find_latest_file_sync("_mapping_*.csv")
        elif file_key == "log_entities": return self._find_latest_file_sync("_entities_*.csv")
        elif file_key == "audit_log":
            p = self.audit_log_file_path
            return p if p.is_file() else None
        logger.warning(f"Tâche {self.job_id}: Clé de fichier inconnue '{file_key}'.")
        return None

    async def read_file_content_async(self, file_path: Path) -> Optional[str]:
        if not await run_in_threadpool(file_path.is_file):
            logger.warning(f"Tâche {self.job_id}: Tentative de lecture d'un fichier inexistant: {file_path}")
            return None
        try:
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f: return await f.read()
        except Exception as e:
            logger.error(f"Tâche {self.job_id}: Erreur de lecture du fichier {file_path.name}: {e}", exc_info=True)
            return None

    def set_initial_status_sync(self) -> bool:
        try:
            self.job_dir.mkdir(parents=True, exist_ok=True)
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                json.dump({"status": "pending", "error": None}, f)
            logger.info(f"Tâche {self.job_id}: Statut initial 'pending' écrit.")
            return True
        except Exception as e:
            logger.error(f"Tâche {self.job_id}: Impossible d'écrire le statut initial: {e}", exc_info=True)
            return False

    def set_status_as_error_sync(self, error_message: str) -> bool:
        try:
            self.job_dir.mkdir(parents=True, exist_ok=True)
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                json.dump({"status": "error", "error": error_message}, f)
            logger.info(f"Tâche {self.job_id}: Statut d'erreur écrit: {error_message}")
            return True
        except Exception as e:
            logger.error(f"Tâche {self.job_id}: Impossible d'écrire le statut d'erreur '{error_message}': {e}", exc_info=True)
            return False

    def set_status_as_finished_sync(self, engine_result: Dict[str, Any]) -> bool:
        status_payload = {"status": "finished", "error": None}
        try:
            self.job_dir.mkdir(parents=True, exist_ok=True)
            with open(self.status_file_path, "w", encoding="utf-8") as f:
                json.dump(status_payload, f)
            with open(self.audit_log_file_path, "w", encoding="utf-8") as f:
                json.dump(engine_result.get("audit_log", []), f)
            logger.info(f"Tâche {self.job_id}: Statut 'finished' et journal d'audit écrits.")
            return True
        except Exception as e:
            logger.error(f"Tâche {self.job_id}: Impossible d'écrire le statut 'finished'/journal d'audit: {e}", exc_info=True)
            self.set_status_as_error_sync(f"Erreur critique: Échec de l'écriture du statut 'finished'/journal d'audit après l'exécution réussie du moteur: {str(e)}")
            return False

    def delete_job_directory_sync(self) -> bool:
        if not self.job_dir.exists():
            logger.warning(f"Tâche {self.job_id}: Tentative de suppression d'un répertoire de tâche inexistant: {self.job_dir}")
            return False
        try:
            shutil.rmtree(self.job_dir)
            logger.info(f"Tâche {self.job_id}: Répertoire {self.job_dir} supprimé avec succès.")
            return True
        except OSError as e:
            logger.error(f"Tâche {self.job_id}: Erreur lors de la suppression du répertoire {self.job_dir}: {e}", exc_info=True)
            return False