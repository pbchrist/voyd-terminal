#!/usr/bin/env python3
"""Run one Hermes-native Voyd Story Room evolution cycle."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = "voyd-story-room"
STATUS_PATH = ROOT / "story_room" / "reports" / "last_run_status.json"


def build_prompt(packet_path: Path) -> str:
    return f"""Run exactly one Voyd Story Room evolution cycle on THIS exact repository: {ROOT}.

Use the voyd-story-room skill as governing procedure. This supersedes the legacy numeric evolve.py promotion rubric.

Requirements:
- FIRST run `pwd` and verify it is exactly `{ROOT}`. If not, stop.
- For child context use the exact files `story_room/STORY_PHYSICS.md`, `story_room/genome.json`, `story_room/ROOM_PROTOCOL.md`, `story_room/walkers/<role>.md`, and the authoritative play packet `{packet_path}`; do not guess root-level aliases.
- Every Phantom Walker must judge `{packet_path}` first. Do not use browser/computer-use/execute_code to rediscover the playable story unless the packet is demonstrably inconsistent with the repository.
- Read the actual playable story, active story_room/genome.json, source-canon boundary, prior reports, and all six walker dossiers FROM `{ROOT}` only.
- Spawn the six Phantom Walkers as real Hermes delegated agents in ONE parallel batch with `background=false`; never background this batch.
- Diagnose the earliest structural wound from evidence.
- Have a separate Structural Editor create 2-4 genuinely different structural mutations using `background=false`.
- Have a separate Canon/Continuity Steward prosecute every mutation using `background=false`.
- Replay surviving mutations through the six logical walker identities.
- Have a separate Acumen Keeper compare survivors against the Story Genome using `background=false`.
- If inherited acumen uniquely decides the fork, select and implement it, then replay-test the implementation.
- If more than one genuinely different structurally valid future survives, DO NOT choose for Patrick. Write story_room/pending_speciation.json with compact A/B/C options in the form structural change -> story consequence -> price, then stop before implementation.
- Never edit source/book canon.
- Never use numeric story-quality averages or tension_delta as proof of drama.
- Never use the legacy forced-archetype Phantom Walker script as a substitute for delegated walkers.
- Do not merge to main or read/write another worktree. Never fall back to `/home/patrick/voyd-terminal`.

Before you exit, ALWAYS write `{STATUS_PATH}` as valid JSON with exactly these fields:
{{
  "status": "passed|pending_speciation|blocked|failed",
  "human_input_required": true_or_false,
  "final_replay": "passed|not_applicable|blocked|failed",
  "summary": "one concise factual sentence"
}}
Rules for that status file:
- `passed` is allowed ONLY after an implemented mutation completes the final six-Phantom replay and all six PASS.
- `pending_speciation` means multiple structurally valid futures survived and Patrick must choose; do not implement any of them.
- `blocked` means provider limits, unavailable tools/models, interrupted delegation, or another external blocker prevented a trustworthy verdict.
- `failed` means the cycle itself failed mechanically or violated a required invariant.
- Never claim `passed` because tests alone passed. The final six-Phantom replay is mandatory.

Persist reports and artifacts under story_room/. End with a concise factual summary of what happened and whether Patrick input is required.
"""


def build_packet() -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    path = ROOT / "story_room" / "packets" / f"{stamp}.json"
    script = ROOT / "scripts" / "build_story_packet.py"
    subprocess.run([sys.executable, str(script), "--output", str(path)], cwd=ROOT, check=True)
    return path


def require_sync_hook(env: dict[str, str]) -> None:
    hermes_home = Path(env.get("HERMES_HOME", Path.home() / ".hermes"))
    delegate_tool = hermes_home / "hermes-agent" / "tools" / "delegate_tool.py"
    marker = "VOYD_FORCE_SYNC_DELEGATION=1: forcing delegate_task background=False"
    if not delegate_tool.exists() or marker not in delegate_tool.read_text(encoding="utf-8"):
        installer = ROOT / "scripts" / "install_hermes_story_room.py"
        raise RuntimeError(
            "Hermes Story Room sync hook is not installed. Run: "
            f"{sys.executable} {installer} --hermes-home {hermes_home}"
        )


def run(max_turns: int) -> int:
    env = os.environ.copy()
    env.setdefault("HERMES_HOME", str(Path.home() / ".hermes"))
    env["VOYD_FORCE_SYNC_DELEGATION"] = "1"
    require_sync_hook(env)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.unlink(missing_ok=True)
    cmd = [
        "hermes", "chat", "-Q", "--in", str(ROOT),
        "--skills", SKILL, "--max-turns", str(max_turns),
        "--query-file", "-",
    ]
    packet_path = build_packet()
    proc = subprocess.run(cmd, input=build_prompt(packet_path), text=True, env=env)
    return proc.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-turns", type=int, default=250)
    args = parser.parse_args(argv)
    started = datetime.now().isoformat()
    print(f"[story-room] starting {started}")
    return run(args.max_turns)


if __name__ == "__main__":
    raise SystemExit(main())
