"""Entry point for the embedded API server (PyInstaller sidecar)."""

from __future__ import annotations

import argparse

import uvicorn

from anonyfiles_api.api import app


def main() -> None:
    parser = argparse.ArgumentParser(prog="anonyfiles-api")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--log-level", default="info")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
