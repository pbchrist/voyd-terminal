#!/usr/bin/env python3
"""Story-only Telegram delivery bridge for the Voyd Story Room.

HermBeast Telegram is a reader/editor surface, not an operations console.
Only accepted reader-facing fiction is delivered. Lifecycle/status boundaries
are suppressed. On a passed cycle, this bridge reads the actual changed
story/scenes/*.md files from the worktree and sends their full reader-facing
text as plain Telegram messages. Patrick can reply naturally with revisions.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
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


def _reader_text(markdown: str) -> str:
    """Keep fiction and choices; remove machine-facing ledger metadata."""
    out: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("**Branch point:") or stripped.startswith("**State created:"):
            continue
        if stripped.startswith("**Canonical") or stripped.startswith("**Frontier"):
            continue
        if stripped == "---":
            continue
        # Turn markdown links into readable plain-text choices.
        line = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line)
        line = line.replace("**", "").replace("*", "")
        if line.startswith("# "):
            line = line[2:]
        elif line.startswith("## "):
            line = line[3:]
        elif line.startswith("### "):
            line = line[4:]
        out.append(line.rstrip())
    # Collapse excessive blank space but keep paragraph breaks.
    text = "\n".join(out).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _blocks(markdown: str) -> list[str]:
    return [b.strip() for b in markdown.split("\n\n") if b.strip()]


def _is_structural(block: str) -> bool:
    return block.startswith(("#", "---", "**Branch", "**State", "**Canonical", "**Frontier"))


def _prose_blocks(markdown: str) -> list[str]:
    """Reader-facing fiction only: no headings, choice links, or frontier notes."""
    out: list[str] = []
    after_frontier_head = False
    for block in _blocks(markdown):
        if block.startswith(("## \u25c9 ACTIVE FRONTIER", "## ACTIVE FRONTIER")):
            after_frontier_head = True
            continue
        if after_frontier_head:
            # The paragraph under the heading is the machine-facing note.
            after_frontier_head = False
            continue
        if block.startswith(("### [", "## Choose")) or _is_structural(block):
            continue
        out.append(block)
    return out


def _choice_blocks(markdown: str) -> list[str]:
    return [b for b in _blocks(markdown) if b.startswith("### [")]


def _scene_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def _text_at_head(rel: str) -> str:
    """The committed version of a scene, or "" when the cycle just created it."""
    proc = subprocess.run(
        ["git", "show", f"HEAD:{rel}"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    return proc.stdout if proc.returncode == 0 else ""


def _changed_story() -> str:
    """Only the prose this cycle actually wrote.

    A scene whose sole edit was its frontier note or a choice link is reported
    as one line instead of being re-sent in full. Reading the same 360 words
    again is how a real change gets buried.
    """
    proc = subprocess.run(
        ["git", "status", "--porcelain", "--", "story/scenes"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    paths: list[str] = []
    for raw in proc.stdout.splitlines():
        rel = raw[3:].strip() if len(raw) > 3 else ""
        if rel.startswith("story/scenes/") and rel.endswith(".md"):
            paths.append(rel)
    # Preserve deterministic narrative order when several scenes changed.
    paths = sorted(dict.fromkeys(paths))

    sections: list[str] = []
    notes: list[str] = []
    for rel in paths:
        path = ROOT / rel
        if not path.exists():
            continue
        new_md = path.read_text(encoding="utf-8")
        old_md = _text_at_head(rel)
        # Several routes can share a scene title; the id keeps them distinct
        # and gives Patrick something exact to reply about.
        title = f"{_scene_title(new_md, path.stem)} ({path.stem.split(chr(45))[0]})"

        old_prose = _prose_blocks(old_md)
        added = [b for b in _prose_blocks(new_md) if b not in old_prose]

        if added:
            label = f"{title} \u2014 NEW SCENE" if not old_md.strip() else f"{title} \u2014 new passage"
            body = _reader_text("\n\n".join(added))
            choices = _choice_blocks(new_md)
            if choices:
                body = f"{body}\n\n{_reader_text(chr(10).join(choices))}"
            sections.append(f"{label}\n\n{body}")
            continue

        old_choices = _choice_blocks(old_md)
        new_choices = _choice_blocks(new_md)
        if new_choices != old_choices:
            fresh = [_reader_text(c).splitlines()[0] for c in new_choices if c not in old_choices]
            if fresh:
                notes.append(f"{title} \u2014 now leads to: " + "; ".join(fresh))
            else:
                notes.append(f"{title} \u2014 choices changed, prose unchanged")
        else:
            notes.append(f"{title} \u2014 frontier note only, prose unchanged")

    parts: list[str] = []
    if sections:
        parts.append("\n\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n".join(sections))
    if notes:
        parts.append("Also touched, no new prose:\n" + "\n".join(f"\u00b7 {n}" for n in notes))
    return "\n\n\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\n\n".join(parts)


def post(boundary: str, detail: str = "") -> dict:
    # Telegram is story-only. Operations remain in logs/status files.
    if boundary != "passed":
        return {"ok": True, "suppressed": True, "boundary": boundary}

    story = _changed_story()
    if not story:
        # Backward-compatible fallback for a cycle whose scene changes were
        # committed earlier than this bridge call.
        marker = "NEW STORY BEAT"
        story = detail.split(marker, 1)[-1].strip() if marker in detail else detail.strip()
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
