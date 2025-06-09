#!/usr/bin/env bash
# Compile project dependencies using pip-tools
set -e
pip-compile requirements.in
# Replace any occurrence of "file://$PWD" in the generated file with a
# relative path so requirements.txt stays portable.
sed -i -e "s|file://$(pwd)/|./|g" -e "s|file://$(pwd)|.|g" requirements.txt
pip-compile requirements-test.in
