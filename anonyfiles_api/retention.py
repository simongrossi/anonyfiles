# anonyfiles_api/retention.py
"""Purge automatique des répertoires de jobs expirés.

Un job conserve sur disque le fichier original **et** le mapping CSV
(la table de dé-anonymisation, donc les PII en clair). Pour un outil dont
le métier est justement l'anonymisation, laisser ces données indéfiniment
est un risque de confidentialité. Ce module supprime les jobs plus vieux
qu'un TTL configurable.

``purge_expired_jobs`` est volontairement synchrone et sans dépendance à
l'app (juste la stdlib) pour rester trivialement testable. ``run_purge_loop``
est la fine couche asynchrone branchée sur le cycle de vie de l'API.
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import time
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("anonyfiles_api.retention")


def purge_expired_jobs(
    jobs_dir: Path,
    max_age_seconds: float,
    now: Optional[float] = None,
) -> List[str]:
    """Supprime les répertoires de jobs plus vieux que ``max_age_seconds``.

    Args:
        jobs_dir: Répertoire racine contenant un sous-dossier par job.
        max_age_seconds: Âge maximal autorisé (basé sur le mtime du dossier).
        now: Horodatage de référence (injectable pour les tests).

    Returns:
        La liste des identifiants de jobs (noms de dossiers) supprimés.
    """
    if max_age_seconds <= 0:
        return []

    jobs_dir = Path(jobs_dir)
    if not jobs_dir.is_dir():
        return []

    reference = time.time() if now is None else now
    deleted: List[str] = []

    for entry in sorted(jobs_dir.iterdir()):
        if not entry.is_dir():
            continue
        try:
            age = reference - entry.stat().st_mtime
        except OSError as exc:
            logger.warning("Rétention: impossible de lire %s (%s).", entry, exc)
            continue
        if age < max_age_seconds:
            continue
        try:
            shutil.rmtree(entry)
            deleted.append(entry.name)
            logger.info(
                "Rétention: job %s supprimé (âge %.0f s > TTL %.0f s).",
                entry.name,
                age,
                max_age_seconds,
            )
        except OSError as exc:
            # Un job en erreur ne doit pas interrompre le balayage des autres.
            logger.error("Rétention: échec suppression %s (%s).", entry, exc)

    return deleted


async def run_purge_loop(
    jobs_dir: Path,
    max_age_seconds: float,
    interval_seconds: float,
    stop_event: asyncio.Event,
) -> None:
    """Balaye ``jobs_dir`` au démarrage puis toutes les ``interval_seconds``.

    S'arrête proprement dès que ``stop_event`` est positionné. La purge tourne
    dans un thread (``asyncio.to_thread``) pour ne pas bloquer la boucle
    d'événements sur de gros répertoires.
    """
    if max_age_seconds <= 0:
        logger.info("Rétention des jobs désactivée (TTL <= 0).")
        return

    logger.info(
        "Rétention des jobs active: TTL %.0f s, balayage toutes les %.0f s.",
        max_age_seconds,
        interval_seconds,
    )
    while not stop_event.is_set():
        try:
            await asyncio.to_thread(purge_expired_jobs, jobs_dir, max_age_seconds)
        except Exception as exc:  # noqa: BLE001 - la boucle ne doit jamais mourir
            logger.error("Rétention: erreur inattendue pendant la purge (%s).", exc)
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_seconds)
        except asyncio.TimeoutError:
            continue
