#!/bin/bash
cd "$(dirname "$0")"
source ~/.hermes/.env 2>/dev/null || true
export ANTHROPIC_API_KEY
PYTHON="${PYTHON:-python3}"
if [ -x .venv/bin/python ]; then
  PYTHON=".venv/bin/python"
fi
"$PYTHON" -m uvicorn engine.main:app --host 127.0.0.1 --port 8765 --reload
