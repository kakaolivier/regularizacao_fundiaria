#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -c 'import sys; assert sys.version_info >= (3, 10), "Use Python 3.10 ou superior"'
python3 -m venv .venv
.venv/bin/python -m pip install --cache-dir .pip-cache --only-binary=:all: -r requirements.txt
.venv/bin/python -m unittest discover -s tests -p 'test_*.py'
printf 'Para iniciar: .venv/bin/python app.py --open\n'
