#!/bin/bash
cd "$(dirname "$0")/frontend"
PYTHON="${PYTHON:-python3}"
if [ -x ../.venv/bin/python ]; then
  PYTHON="../.venv/bin/python"
fi
"$PYTHON" -m http.server 8765
