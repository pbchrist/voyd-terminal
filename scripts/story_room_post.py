#!/usr/bin/env python3
"""Story-only Telegram delivery bridge for the Voyd Story Room.

HermBeast Telegram is a reader/editor surface, not an operations console.
Only accepted reader-facing fiction is delivered. Lifecycle/status boundaries
are intentionally suppressed. Story text is sent as plain text and split into
Telegram-safe chunks. Patrick can reply naturally with revision directions.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

HERMBEAST_HOME = Path("/home/patrick/.hermes")
FORBIDDEN_HERMIONE_HOME = Path("/home/patrick/hermes-instance2")
MAX_MESSAGE = 3900
BOUNDARIES = {"start", "finished", "passed", "blocked", "failed", "decision", "pending_speciation"}


class PostError(RuntimeError):
    pass


def _read_env_file(path: Path) -> dict[str, str]:
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
    hermes_home = Path(os.environ.get("HERMES_HOME", str(HERMBEAST_HOME)))
    if hermes_home.resolve() == FORBIDDEN_HERMIONE_HOME.resolve():
        raise PostError("refusing to post from Hermione")
    if hermes_home.resolve() != HERMBEAST_HOME.resolve():
        raise PostError(f"expected HermBeast at {HERMBEAST_HOME}; got {hermes_home}")
    identity = HERMBEAST_HOME / ".instance-id"
    value = identity.read_text(encoding="utf-8").strip() if identity.exists() else ""
    if value != "HERMBEAST":
        raise PostError(f"HermBeast identity not confirmed: {value!r}")


def _load_credentials() -> tuple[str, str]:
    env = _read_env_file(HERMBEAST_HOME / ".env")
    token = env.get("TELEGRAM_BOT_TOKEN") or os.environ.get("TELEGRAM_BOT_TOKEN", "")
    home = env.get("TELEGRAM_HOME_CHANNEL") or os.environ.get("TELEGRAM_HOME_CHANNEL", "")
    if not token or not home:
        raise PostError("HermBeast Telegram credentials are missing")
    return token, home


def _telegram_api(token: str, payload: dict, timeout: int = 30) -> dict:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _chunks(text: str) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks: list[str] = []
    while len(text) > MAX_MESSAGE:
        cut = text.rfind("\n\n", 0, MAX_MESSAGE)
        if cut < MAX_MESSAGE // 2:
            cut = text.rfind("\n", 0, MAX_MESSAGE)
        if cut < MAX_MESSAGE // 2:
            cut = MAX_MESSAGE
        chunks.append(text[:cut].rstrip())
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def post(boundary: str, detail: str = "") -> dict:
    # Patrick asked for Telegram to contain the fiction and nothing else.
    # Suppress all operational lifecycle messages.
    if boundary != "passed":
        return {"ok": True, "suppressed": True, "boundary": boundary}

    story = detail.strip()
    if not story:
        raise PostError("passed cycle contained no reader-facing story text")

    verify_hermbeast_identity()
    token, home = _load_credentials()
    parts = _chunks(story)
    parts[-1] = parts[-1].rstrip() + "\n\nReply in plain language with anything you want changed."

    last_result: dict = {"ok": False}
    for part in parts:
        payload = {"chat_id": home, "text": part}
        last_err = None
        for attempt in range(1, 4):
            try:
                result = _telegram_api(token, payload)
                if result.get("ok"):
                    last_result = result
                    break
                last_err = result.get("description")
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
            time.sleep(2 * attempt)
        else:
            raise PostError(f"failed to send story after retries: {last_err}")
    return last_result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="HermBeast story-only Telegram bridge")
    parser.add_argument("--boundary", required=True, choices=sorted(BOUNDARIES))
    parser.add_argument("--detail", default="")
    args = parser.parse_args(argv)
    try:
        post(args.boundary, args.detail)
    except PostError as exc:
        print(f"[story-room-post] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
