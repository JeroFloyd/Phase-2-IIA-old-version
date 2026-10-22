#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"
python -m streamlit run gui/app.py
