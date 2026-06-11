#!/bin/bash
# Stop hook: keep docs/STATE.md current (session-handoff freshness).
# Blocks the stop once with a reminder when the repo has changed meaningfully
# more recently than STATE.md. See docs/STATE.md for why this exists.

input=$(cat)
# Already continuing because of this hook? Allow the stop — never loop.
echo "$input" | jq -e '.stop_hook_active == true' >/dev/null 2>&1 && exit 0

cd "$(dirname "$0")/../.." || exit 0
state_file="docs/STATE.md"
[ -f "$state_file" ] || exit 0

state_m=$(stat -c %Y "$state_file" 2>/dev/null || echo 0)
newest=0

# Newest uncommitted change (tracked or untracked), excluding STATE.md itself
while IFS= read -r f; do
  [ "$f" = "$state_file" ] && continue
  [ -f "$f" ] || continue
  m=$(stat -c %Y "$f" 2>/dev/null || echo 0)
  [ "$m" -gt "$newest" ] && newest=$m
done < <(git status --porcelain=v1 --untracked-files=all 2>/dev/null | sed -e 's/^...//' -e 's/^"\(.*\)"$/\1/')

# Newest commit counts too, unless that commit already touched STATE.md
head_t=$(git log -1 --format=%ct 2>/dev/null || echo 0)
if [ "$head_t" -gt "$newest" ]; then
  if ! git log -1 --name-only --format= 2>/dev/null | grep -qx "$state_file"; then
    newest=$head_t
  fi
fi

# Stale = repo changed more than 20 minutes after STATE.md was last touched.
# The 20-minute grace keeps rapid mid-session iteration from nagging every turn.
if [ "$newest" -gt $((state_m + 1200)) ]; then
  echo '{"decision":"block","reason":"The repo has changed since docs/STATE.md was last updated. Before finishing: update docs/STATE.md (session log entry, current state, next steps). If the changes came from background cron activity rather than this session, note that briefly instead. Then stop."}'
fi
exit 0
