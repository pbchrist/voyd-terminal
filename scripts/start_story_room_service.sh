#!/usr/bin/env bash
set -euo pipefail

ROOT=/home/patrick/voyd-story-engine
cd "$ROOT"

# This is a dedicated autonomous worktree. If a previous interrupted Story Room
# attempt left tracked/untracked mutation residue behind, preserve a patch for
# forensics and restore the committed branch before the supervisor starts.
if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  backup="/tmp/voyd-story-room-interrupted-${stamp}.patch"
  {
    echo "# Interrupted Voyd Story Room worktree snapshot: ${stamp}"
    git status --short
    echo
    git diff --binary
    git diff --cached --binary
  } > "$backup" || true
  echo "[story-room] recovering dirty autonomous worktree; snapshot saved to $backup"
  git reset --hard HEAD
  git clean -fd
fi

exec /usr/bin/python3 "$ROOT/scripts/autonomous_story_room.py"
