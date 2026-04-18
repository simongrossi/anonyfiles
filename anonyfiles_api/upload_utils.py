# anonyfiles_api/upload_utils.py
"""Utilities for safely handling uploaded files.

Centralises two concerns that the routers previously mixed with business logic:

* ``safe_upload_filename`` hardens filename handling against path traversal,
  null bytes, Windows-style absolute paths and empty/degenerate inputs.
* ``stream_upload_to_path`` streams an ``UploadFile`` to disk in chunks while
  enforcing a maximum byte count, raising ``UploadTooLargeError`` as soon as
  the limit is exceeded so we never materialise a giant upload on disk.
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Optional

import aiofiles
from fastapi import UploadFile


DEFAULT_CHUNK_SIZE = 1024 * 1024  # 1 MiB


class UploadTooLargeError(Exception):
    """Raised when an uploaded file exceeds the configured maximum size."""

    def __init__(self, max_bytes: int):
        super().__init__(
            f"Uploaded file exceeds the maximum allowed size ({max_bytes} bytes)."
        )
        self.max_bytes = max_bytes


def safe_upload_filename(
    raw_filename: Optional[str],
    *,
    fallback_stem: str = "upload",
    fallback_suffix: str = ".tmp",
) -> str:
    """Return a safe basename derived from ``raw_filename``.

    Strips directory components (POSIX *and* Windows-style), rejects null
    bytes, collapses reserved names (``.``, ``..``) to the fallback and
    guarantees a non-empty return value. The caller is expected to join the
    result with a trusted directory — the returned value never contains a
    path separator.
    """

    fallback = f"{fallback_stem}{fallback_suffix}"
    if not raw_filename:
        return fallback

    if "\x00" in raw_filename:
        return fallback

    # Treat both POSIX and Windows separators to defeat cross-platform tricks
    # (e.g. uploading "..\\evil.txt" from a Windows client against a Linux
    # server).
    posix_name = PurePosixPath(raw_filename).name
    windows_name = PureWindowsPath(raw_filename).name
    candidate = windows_name if len(windows_name) < len(posix_name) else posix_name
    candidate = candidate.strip()

    if not candidate or candidate in {".", ".."}:
        return fallback

    # Final safety net: if anything still looks like a path component, bail.
    if os.sep in candidate or (os.altsep and os.altsep in candidate):
        return fallback

    return candidate


async def stream_upload_to_path(
    upload_file: UploadFile,
    destination: Path,
    *,
    max_bytes: Optional[int] = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> int:
    """Stream ``upload_file`` to ``destination``, enforcing ``max_bytes``.

    Returns the number of bytes written. Raises ``UploadTooLargeError`` and
    removes the partial file if the limit is exceeded.
    """

    total = 0
    async with aiofiles.open(destination, "wb") as buffer:
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if max_bytes is not None and total > max_bytes:
                await buffer.close()
                try:
                    destination.unlink()
                except OSError:
                    pass
                raise UploadTooLargeError(max_bytes)
            await buffer.write(chunk)
    return total
