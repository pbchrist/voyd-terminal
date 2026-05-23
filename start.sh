#!/bin/bash
cd "$(dirname "$0")"
source ~/.hermes/.env 2>/dev/null || true
export ANTHROPIC_API_KEY
python3 -m uvicorn engine.main:app --host 127.0.0.1 --port 8765 --reload
