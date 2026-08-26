#!/usr/bin/env python3
"""Visible HermBeast post bridge for the Voyd Story Room.

The Story Room must announce itself to Patrick through a VISIBLE post on the
HermBeast Telegram bot — not a hidden `hermes chat -Q` process, not Qwen output,
not a systemd log line, not a GitHub commit, and not a status JSON. This module
is the single, explicit mechanism that creates those posts.

Identity safety:
- It only posts when the HermBeast instance identity is confirmed
  (`/home/patrick/.hermes/.instance-id` == "HERMBEAST").
- It hard-refuses to run under the Hermione instance
  (`/home/patrick/hermes-instance2`, .instance-id "HERMIONE").
- It reads the bot token from HermBeast's own `~/.hermes/.env`
  (TELEGRAM_BOT_TOKEN) and the home channel from TELEGRAM_HOME_CHANNEL,
  so the post is produced by the live HermBeast gateway identity.

Usage:
    python3 story_room_post.py --boundary start --detail "..."
    python3 story_room_post.py --boundary finished --detail "..."
    python3 story_room_post.py --boundary blocked --detail "..."
    python3 story_room_post.py --boundary failed --detail "..."
    python3 story_room_post.py --boundary decision --detail "..."

A post failure is a hard error (non-zero exit) so the supervisor can never
silently skip the announcement.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERMBEAST_HOME = Path("/home/patrick/.hermes")
FORBIDDEN_HERMIONE_HOME = Path("/home/patrick/hermes-instance2")

BOUNDARY_EMOJI = {
    "start": "🚀",
    "finished": "✅",
    "passed": "✅",
    "blocked": "🛑",
    "failed": "❌",
    "decision": "⚖️",
    "pending_speciation": "⚖️",
}
BOUNDARY_LABEL = {
    "start": "STORY ROOM STARTING",
    "finished": "STORY ROOM FINISHED",
    "passed": "STORY ROOM PASSED",
    "blocked": "STORY ROOM BLOCKED",
    "failed": "STORY ROOM FAILED",
    "decision": "NEEDS PATRICK'S DECISION",
    "pending_speciation": "NEEDS PATRICK'S DECISION",
}


class PostError(RuntimeError):
    pass


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=VALUE lines from a .env file (no external deps)."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key:
            values[key] = val
    return values


def verify_hermbeast_identity() -> None:
    """Hard gate: only the HermBeast instance may post for the Voyd Story Room."""
    hermes_home = Path(os.environ.get("HERMES_HOME", str(HERMBEAST_HOME)))
    if hermes_home.resolve() == FORBIDDEN_HERMIONE_HOME.resolve():
        raise PostError("refusing to post from the Hermione instance (HERMES_HOME=hermes-instance2)")
    if hermes_home.resolve() != HERMBEAST_HOME.resolve():
        raise PostError(
            f"Voyd Story Room posts must come from HermBeast at {HERMBEAST_HOME}; "
            f"got HERMES_HOME={hermes_home}"
        )
    instance_id_file = HERMBEAST_HOME / ".instance-id"
    instance_id = instance_id_file.read_text(encoding="utf-8").strip() if instance_id_file.exists() else ""
    if instance_id != "HERMBEAST":
        raise PostError(f"HermBeast identity not confirmed: .instance-id={instance_id!r}")


def _load_credentials() -> tuple[str, str]:
    env = _read_env_file(HERMBEAST_HOME / ".env")
    token = env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    home = env.get("TELEGRAM_HOME_CHANNEL") or os.environ.get("TELEGRAM_HOME_CHANNEL", "")
    if not token:
        raise PostError("TELEGRAM_BOT_TOKEN not found in HermBeast ~/.hermes/.env")
    if not home:
        raise PostError("TELEGRAM_HOME_CHANNEL not found in HermBeast ~/.hermes/.env")
    return token, home


def _telegram_api(method: str, token: str, payload: dict, timeout: int = 30) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post(boundary: str, detail: str = "") -> dict:
    """Send one visible HermBeast Telegram post. Raises PostError on any failure."""
    verify_hermbeast_identity()
    token, home = _load_credentials()

    emoji = BOUNDARY_EMOJI.get(boundary, "📣")
    label = BOUNDARY_LABEL.get(boundary, boundary.upper())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    branch = os.environ.get("VOYD_AUTONOMOUS_BRANCH", "feat/story-engine-v2")

    # Plain text (no parse_mode) is used deliberately: it is deterministic and
    # immune to Markdown escaping bugs, so arbitrary detail (paths, hashes,
    # model names) can never break delivery. Emojis and line structure keep the
    # post clearly readable and unmistakably visible in the chat.
    lines = [
        f"{emoji} Voyd Story Room — {label}",
        f"Time: {now}",
        "Identity: HermBeast only",
    ]
    if detail:
        lines.append("")
        lines.append(detail.strip())
    lines.append("")
    lines.append(f"branch: {branch}")
    text = "\n".join(lines)

    payload = {
        "chat_id": home,
        "text": text,
    }
    last_err = None
    for attempt in range(1, 4):
        try:
            result = _telegram_api("sendMessage", token, payload)
            if result.get("ok"):
                return result
            last_err = f"Telegram API returned not-ok: {result.get('description')}"
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)
        time.sleep(2 * attempt)
    raise PostError(f"failed to send visible post after retries: {last_err}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Visible HermBeast Story Room post bridge")
    parser.add_argument("--boundary", required=True,
                        choices=sorted(set(list(BOUNDARY_LABEL) + ["start"])))
    parser.add_argument("--detail", default="", help="extra lines to include in the post")
    args = parser.parse_args(argv)
    try:
        post(args.boundary, args.detail)
    except PostError as exc:
        # Log locally so the supervisor has a trace, but FAIL LOUDLY (non-zero)
        # so a missing post can never be mistaken for a delivered one.
        print(f"[story-room-post] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
