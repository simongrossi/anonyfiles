#!/usr/bin/env bash
# Compile project dependencies using pip-tools
set -e
pip-compile requirements.in
pip-compile requirements-test.in
