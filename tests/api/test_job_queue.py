import asyncio
import time

import anonyfiles_api.core_config as core_config
from anonyfiles_api.job_queue import JobQueue
from anonyfiles_api.job_utils import Job


def test_job_queue_retries_failed_job(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path
    attempts = {"count": 0}

    def flaky_job(job_id):
        attempts["count"] += 1
        job = Job(job_id)
        if attempts["count"] == 1:
            job.set_status_as_error_sync("boom")
        else:
            job.set_status_as_finished_sync({"audit_log": []})

    async def scenario():
        queue = JobQueue(retry_attempts=1, timeout_seconds=None)
        await queue.start()
        job_id = "retry-job"
        Job(job_id).set_initial_status_sync()
        await queue.enqueue(
            job_id=job_id,
            kind="test",
            func=flaky_job,
            kwargs={"job_id": job_id},
        )
        await queue.join()
        await queue.stop()
        return await Job(job_id).get_status_async()

    try:
        status_payload = asyncio.run(scenario())
    finally:
        core_config.JOBS_DIR = original_jobs_dir

    assert attempts["count"] == 2
    assert status_payload["status"] == "finished"
    assert status_payload["attempt"] == 2
    assert status_payload["progress"] == 100


def test_job_queue_cancels_queued_job(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path

    def never_run():
        raise AssertionError("queued job should not run")

    async def scenario():
        queue = JobQueue()
        job_id = "cancel-job"
        Job(job_id).set_initial_status_sync()
        await queue.enqueue(
            job_id=job_id,
            kind="test",
            func=never_run,
            kwargs={},
        )
        cancelled = await queue.cancel(job_id)
        return cancelled, await Job(job_id).get_status_async()

    try:
        cancelled, status_payload = asyncio.run(scenario())
    finally:
        core_config.JOBS_DIR = original_jobs_dir

    assert cancelled is True
    assert status_payload["status"] == "cancelled"
    assert status_payload["state"] == "cancelled"


def test_job_queue_timeout_protects_terminal_status(tmp_path):
    original_jobs_dir = core_config.JOBS_DIR
    core_config.JOBS_DIR = tmp_path

    def slow_job(job_id):
        time.sleep(0.2)
        Job(job_id).set_status_as_finished_sync({"audit_log": []})

    async def scenario():
        queue = JobQueue(timeout_seconds=0.05)
        await queue.start()
        job_id = "timeout-job"
        Job(job_id).set_initial_status_sync()
        await queue.enqueue(
            job_id=job_id,
            kind="test",
            func=slow_job,
            kwargs={"job_id": job_id},
        )
        await queue.join()
        status_after_timeout = await Job(job_id).get_status_async()
        await asyncio.sleep(0.25)
        status_after_thread_exit = await Job(job_id).get_status_async()
        await queue.stop()
        return status_after_timeout, status_after_thread_exit

    try:
        status_after_timeout, status_after_thread_exit = asyncio.run(scenario())
    finally:
        core_config.JOBS_DIR = original_jobs_dir

    assert status_after_timeout["status"] == "timeout"
    assert status_after_thread_exit["status"] == "timeout"
