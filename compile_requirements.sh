#!/usr/bin/env bash
# Compile the single runtime lock from pyproject.toml using pip-tools.
set -euo pipefail
python -m piptools compile pyproject.toml -o requirements.txt
