#!/bin/bash
# Keeps the Voyd's shared body alive. Cron-safe (flock prevents stampedes).
cd "$(dirname "$0")/.." || exit 1
exec 9>logs/.voyd_server.lock
flock -n 9 || exit 0
if ! pgrep -f "python3 voyd_server.py" >/dev/null; then
  mkdir -p logs
  nohup python3 voyd_server.py >> logs/voyd_server.log 2>&1 &
  echo "$(date -Is) voyd_server resurrected" >> logs/voyd_server.log
fi
