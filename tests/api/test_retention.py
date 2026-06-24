import asyncio
import os
import time

from anonyfiles_api.retention import purge_expired_jobs, run_purge_loop


def _make_job(jobs_dir, name, age_seconds, now):
    job_dir = jobs_dir / name
    job_dir.mkdir(parents=True)
    (job_dir / "status.json").write_text('{"status": "finished"}', encoding="utf-8")
    (job_dir / "input_mapping.csv").write_text("Jean Dupont,PER_1", encoding="utf-8")
    # Vieillit le répertoire en reculant son mtime.
    old = now - age_seconds
    os.utime(job_dir, (old, old))
    return job_dir


def test_purge_deletes_only_expired_jobs(tmp_path):
    now = time.time()
    fresh = _make_job(tmp_path, "fresh", age_seconds=60, now=now)
    expired = _make_job(tmp_path, "expired", age_seconds=3 * 3600, now=now)

    deleted = purge_expired_jobs(tmp_path, max_age_seconds=3600, now=now)

    assert deleted == ["expired"]
    assert fresh.exists()
    assert not expired.exists()


def test_purge_returns_empty_when_nothing_expired(tmp_path):
    now = time.time()
    _make_job(tmp_path, "a", age_seconds=10, now=now)
    _make_job(tmp_path, "b", age_seconds=20, now=now)

    deleted = purge_expired_jobs(tmp_path, max_age_seconds=3600, now=now)

    assert deleted == []
    assert (tmp_path / "a").exists()
    assert (tmp_path / "b").exists()


def test_purge_ignores_non_directories_and_missing_dir(tmp_path):
    now = time.time()
    stray = tmp_path / "stray.txt"
    stray.write_text("not a job", encoding="utf-8")
    os.utime(stray, (now - 10000, now - 10000))

    deleted = purge_expired_jobs(tmp_path, max_age_seconds=3600, now=now)
    assert deleted == []
    assert stray.exists()

    # Un dossier jobs inexistant ne doit pas lever.
    assert purge_expired_jobs(tmp_path / "does-not-exist", max_age_seconds=3600) == []


def test_run_purge_loop_sweeps_then_stops(tmp_path):
    now = time.time()
    expired = _make_job(tmp_path, "old", age_seconds=10000, now=now)

    async def scenario():
        stop = asyncio.Event()
        task = asyncio.create_task(
            run_purge_loop(
                tmp_path,
                max_age_seconds=3600,
                interval_seconds=0.05,
                stop_event=stop,
            )
        )
        await asyncio.sleep(0.15)  # laisse le temps d'au moins un balayage
        stop.set()
        await asyncio.wait_for(task, timeout=2)

    asyncio.run(scenario())
    assert not expired.exists()


def test_run_purge_loop_disabled_keeps_everything(tmp_path):
    now = time.time()
    expired = _make_job(tmp_path, "old", age_seconds=10000, now=now)

    async def scenario():
        stop = asyncio.Event()
        # TTL <= 0 => purge désactivée, la coroutine retourne immédiatement.
        await asyncio.wait_for(
            run_purge_loop(
                tmp_path, max_age_seconds=0, interval_seconds=0.05, stop_event=stop
            ),
            timeout=2,
        )

    asyncio.run(scenario())
    assert expired.exists()
