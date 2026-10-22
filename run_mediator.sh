#!/usr/bin/env bash
set -euo pipefail

# Load .env when present so the mediator can target local Docker and remote native MySQL sources.
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export PYTHONPATH="$(pwd)${PYTHONPATH:+:$PYTHONPATH}"
python -m uvicorn mediator.main:app --host 0.0.0.0 --port 8000
