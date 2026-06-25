import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

from .core_config import logger
from .job_utils import Job, TERMINAL_JOB_STATUSES, log_job_event, utc_now_iso


@dataclass(slots=True)
class QueuedJob:
    job_id: str
    kind: str
    func: Callable[..., None]
    kwargs: dict[str, Any]
    timeout_seconds: Optional[float]
    retry_attempts: int
    retry_delay_seconds: float
    enqueued_at: str = field(default_factory=utc_now_iso)


class JobQueue:
    """Small in-process job queue for API background work.

    The queue keeps the public API responsive while making job lifecycle
    transitions explicit in ``status.json``. Running work is synchronous and
    executed in a worker thread, so cancellation is immediate for queued jobs
    and cooperative for already-running jobs: the public status is protected as
    ``cancelled``/``timeout`` even if the worker thread returns later.
    """

    def __init__(
        self,
        *,
        worker_count: int = 1,
        timeout_seconds: Optional[float] = None,
        retry_attempts: int = 0,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        self.worker_count = max(1, worker_count)
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds and timeout_seconds > 0 else None
        )
        self.retry_attempts = max(0, retry_attempts)
        self.retry_delay_seconds = max(0.0, retry_delay_seconds)
        self._queue: asyncio.Queue[QueuedJob] = asyncio.Queue()
        self._workers: list[asyncio.Task[None]] = []
        self._pending: dict[str, QueuedJob] = {}
        self._running: dict[str, QueuedJob] = {}
        self._cancel_requested: set[str] = set()
        self._lock = asyncio.Lock()
        self._stopping = False

    @property
    def is_running(self) -> bool:
        return any(not worker.done() for worker in self._workers) and not self._stopping

    async def start(self) -> None:
        self._workers = [worker for worker in self._workers if not worker.done()]
        if self._workers:
            return
        self._stopping = False
        for index in range(self.worker_count):
            self._workers.append(asyncio.create_task(self._worker(index)))
        logger.info("File de jobs API démarrée avec %s worker(s).", self.worker_count)

    async def stop(self, timeout_seconds: float = 5.0) -> None:
        self._stopping = True
        await self._cancel_open_jobs_on_shutdown()
        for worker in self._workers:
            worker.cancel()
        if self._workers:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._workers, return_exceptions=True),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Arrêt de la file de jobs: timeout après %ss.", timeout_seconds
                )
        self._workers.clear()
        async with self._lock:
            self._running.clear()

    async def enqueue(
        self,
        *,
        job_id: str,
        kind: str,
        func: Callable[..., None],
        kwargs: dict[str, Any],
        timeout_seconds: Optional[float] = None,
        retry_attempts: Optional[int] = None,
    ) -> None:
        if self._stopping:
            raise RuntimeError("La file de jobs est en cours d'arrêt.")

        queued_job = QueuedJob(
            job_id=job_id,
            kind=kind,
            func=func,
            kwargs=kwargs,
            timeout_seconds=(
                self.timeout_seconds if timeout_seconds is None else timeout_seconds
            ),
            retry_attempts=(
                self.retry_attempts
                if retry_attempts is None
                else max(0, retry_attempts)
            ),
            retry_delay_seconds=self.retry_delay_seconds,
        )

        async with self._lock:
            self._pending[job_id] = queued_job
            queue_position = self._queue.qsize() + 1

        await Job(job_id).update_status_async(
            status="pending",
            state="queued",
            progress=0,
            error=None,
            job_kind=kind,
            queued_at=queued_job.enqueued_at,
            queue_position=queue_position,
            attempt=0,
            max_attempts=queued_job.retry_attempts + 1,
            timeout_seconds=queued_job.timeout_seconds,
        )
        await self._queue.put(queued_job)
        log_job_event(
            "info",
            "job_queued",
            job_id,
            job_kind=kind,
            queue_position=queue_position,
            max_attempts=queued_job.retry_attempts + 1,
            timeout_seconds=queued_job.timeout_seconds,
        )
        logger.info("Tâche %s (%s) ajoutée à la file.", job_id, kind)

    async def cancel(self, job_id: str, reason: str = "Annulation demandée.") -> bool:
        job = Job(job_id)
        status_payload = await job.get_status_async()
        if status_payload is None:
            return False
        if status_payload.get("status") in TERMINAL_JOB_STATUSES:
            return False

        async with self._lock:
            self._cancel_requested.add(job_id)
            is_pending = job_id in self._pending
            is_running = job_id in self._running
            if is_pending and not is_running:
                self._pending.pop(job_id, None)

        if is_pending and not is_running:
            await self._mark_cancelled(job_id, reason=reason)
        elif is_running:
            await job.update_status_async(
                status="pending",
                state="cancelling",
                progress=status_payload.get("progress", 0),
                cancellation_requested_at=utc_now_iso(),
                error=None,
            )
        else:
            await self._mark_cancelled(
                job_id, reason="Tâche absente de la file active."
            )
            async with self._lock:
                self._cancel_requested.discard(job_id)
        logger.info("Annulation demandée pour la tâche %s.", job_id)
        return True

    async def stats(self) -> dict[str, int]:
        async with self._lock:
            return {
                "queued": len(self._pending),
                "running": len(self._running),
                "workers": len(self._workers),
            }

    async def join(self) -> None:
        await self._queue.join()

    async def _worker(self, index: int) -> None:
        logger.info("Worker de jobs API #%s prêt.", index)
        try:
            while True:
                queued_job = await self._queue.get()
                try:
                    await self._run_job(queued_job)
                finally:
                    self._queue.task_done()
        except asyncio.CancelledError:
            logger.info("Worker de jobs API #%s arrêté.", index)
            raise

    async def _run_job(self, queued_job: QueuedJob) -> None:
        async with self._lock:
            self._pending.pop(queued_job.job_id, None)
            self._running[queued_job.job_id] = queued_job

        try:
            if await self._is_cancel_requested(queued_job.job_id):
                await self._mark_cancelled(
                    queued_job.job_id, reason="Tâche annulée avant démarrage."
                )
                return

            for attempt in range(1, queued_job.retry_attempts + 2):
                should_retry = await self._run_attempt(queued_job, attempt)
                if not should_retry:
                    return
                await asyncio.sleep(queued_job.retry_delay_seconds)
        finally:
            async with self._lock:
                self._running.pop(queued_job.job_id, None)
                self._cancel_requested.discard(queued_job.job_id)

    async def _run_attempt(self, queued_job: QueuedJob, attempt: int) -> bool:
        job = Job(queued_job.job_id)
        log_job_event(
            "info",
            "job_attempt_started",
            queued_job.job_id,
            job_kind=queued_job.kind,
            attempt=attempt,
            max_attempts=queued_job.retry_attempts + 1,
            timeout_seconds=queued_job.timeout_seconds,
        )
        await job.update_status_async(
            status="pending",
            state="running",
            progress=10,
            attempt=attempt,
            started_at=utc_now_iso(),
            error=None,
        )

        try:
            runner = asyncio.to_thread(queued_job.func, **queued_job.kwargs)
            if queued_job.timeout_seconds:
                await asyncio.wait_for(runner, timeout=queued_job.timeout_seconds)
            else:
                await runner
        except asyncio.TimeoutError:
            await job.update_status_async(
                protect_terminal=False,
                status="timeout",
                state="timeout",
                progress=100,
                error=f"Timeout après {queued_job.timeout_seconds} secondes.",
                final_status_category="timeout",
                completed_at=utc_now_iso(),
                attempt=attempt,
            )
            async with self._lock:
                self._cancel_requested.add(queued_job.job_id)
            status_payload = await job.get_status_async() or {}
            self._log_job_finished(queued_job, status_payload)
            return False
        except Exception as exc:  # noqa: BLE001
            await job.set_status_as_error_async(
                f"Erreur inattendue dans la file de jobs: {exc}",
                final_status_category="unexpected_error",
            )

        if await self._is_cancel_requested(queued_job.job_id):
            await self._mark_cancelled(queued_job.job_id, reason="Tâche annulée.")
            status_payload = await job.get_status_async() or {}
            self._log_job_finished(queued_job, status_payload)
            return False

        status_payload = await job.get_status_async() or {}
        status = status_payload.get("status")
        if status == "finished":
            await job.update_status_async(
                state="completed",
                progress=100,
                completed_at=status_payload.get("completed_at", utc_now_iso()),
                attempt=attempt,
            )
            status_payload = await job.get_status_async() or {}
            self._log_job_finished(queued_job, status_payload)
            return False

        if status == "error" and attempt <= queued_job.retry_attempts:
            await job.update_status_async(
                protect_terminal=False,
                status="pending",
                state="retrying",
                progress=20,
                retry_after_seconds=queued_job.retry_delay_seconds,
                last_error=status_payload.get("error"),
                error=None,
                attempt=attempt,
                completed_at=None,
                duration_seconds=None,
                final_status_category=None,
            )
            logger.warning(
                "Tâche %s en échec, nouvelle tentative %s/%s.",
                queued_job.job_id,
                attempt + 1,
                queued_job.retry_attempts + 1,
            )
            log_job_event(
                "warning",
                "job_retry_scheduled",
                queued_job.job_id,
                job_kind=queued_job.kind,
                attempt=attempt,
                next_attempt=attempt + 1,
                max_attempts=queued_job.retry_attempts + 1,
                retry_after_seconds=queued_job.retry_delay_seconds,
                last_error=status_payload.get("error"),
            )
            return True

        if status not in TERMINAL_JOB_STATUSES:
            await job.set_status_as_error_async(
                "La tâche s'est terminée sans écrire de statut terminal.",
                final_status_category="unexpected_error",
            )
            status_payload = await job.get_status_async() or {}
        if status_payload.get("status") in TERMINAL_JOB_STATUSES:
            self._log_job_finished(queued_job, status_payload)
        return False

    def _log_job_finished(
        self, queued_job: QueuedJob, status_payload: dict[str, Any]
    ) -> None:
        level = "info" if status_payload.get("status") == "finished" else "warning"
        log_job_event(
            level,
            "job_finished",
            queued_job.job_id,
            job_kind=queued_job.kind,
            status=status_payload.get("status"),
            state=status_payload.get("state"),
            final_status_category=status_payload.get("final_status_category"),
            attempt=status_payload.get("attempt"),
            max_attempts=status_payload.get("max_attempts"),
            duration_seconds=status_payload.get("duration_seconds"),
            queue_wait_seconds=status_payload.get("queue_wait_seconds"),
            phase_durations_seconds=status_payload.get("phase_durations_seconds"),
            file_size_bytes=status_payload.get("file_size_bytes"),
            file_type=status_payload.get("file_type"),
            entities_detected_count=status_payload.get("entities_detected_count"),
            total_replacements=status_payload.get("total_replacements"),
            error=status_payload.get("error"),
        )

    async def _is_cancel_requested(self, job_id: str) -> bool:
        async with self._lock:
            return job_id in self._cancel_requested

    async def _mark_cancelled(self, job_id: str, reason: str) -> None:
        await Job(job_id).update_status_async(
            protect_terminal=False,
            status="cancelled",
            state="cancelled",
            progress=100,
            error=reason,
            final_status_category="cancelled",
            completed_at=utc_now_iso(),
        )

    async def _cancel_open_jobs_on_shutdown(self) -> None:
        async with self._lock:
            pending_ids = list(self._pending)
            running_ids = list(self._running)
            for job_id in pending_ids:
                self._cancel_requested.add(job_id)
            for job_id in running_ids:
                self._cancel_requested.add(job_id)
            self._pending.clear()
        for job_id in pending_ids:
            await self._mark_cancelled(job_id, reason="Arrêt serveur avant exécution.")
        for job_id in running_ids:
            await self._mark_cancelled(
                job_id, reason="Arrêt serveur pendant l'exécution."
            )


async def ensure_job_queue(app: Any) -> JobQueue:
    job_queue = getattr(app.state, "job_queue", None)
    if job_queue is not None:
        if not job_queue.is_running:
            await job_queue.start()
        return job_queue

    settings = getattr(app.state, "settings", None)
    job_queue = JobQueue(
        worker_count=getattr(settings, "job_worker_count", 1),
        timeout_seconds=getattr(settings, "job_timeout_seconds", 1800),
        retry_attempts=getattr(settings, "job_retry_attempts", 0),
    )
    app.state.job_queue = job_queue
    await job_queue.start()
    return job_queue
