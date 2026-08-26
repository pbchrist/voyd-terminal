#!/usr/bin/env python3
"""Run one HermBeast-native Voyd Story Room evolution cycle with local failover."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = "voyd-story-room"
STATUS_PATH = ROOT / "story_room" / "reports" / "last_run_status.json"
RESUME_PATH = ROOT / "story_room" / "resume_speciation.json"
HERMBEAST_HOME = Path("/home/patrick/.hermes")
FORBIDDEN_HERMIONE_HOME = Path("/home/patrick/hermes-instance2")
HERMBEAST_PATH = ":".join([
    "/home/patrick/.hermes/hermes-agent/venv/bin",
    "/home/patrick/.hermes/hermes-agent/node_modules/.bin",
    "/home/patrick/.hermes/node/bin",
    "/home/patrick/.hermes/node",
    "/home/patrick/.local/bin",
    "/usr/local/sbin",
    "/usr/local/bin",
    "/usr/sbin",
    "/usr/bin",
    "/sbin",
    "/bin",
])


def load_resume() -> dict | None:
    if not RESUME_PATH.exists():
        return None
    marker = json.loads(RESUME_PATH.read_text(encoding="utf-8"))
    decision_file = ROOT / marker["decision_file"]
    decision = json.loads(decision_file.read_text(encoding="utf-8"))
    if decision["decision"]["selected"] != marker["selected"]:
        raise RuntimeError("resume marker does not match recorded Patrick decision")
    return decision


def build_prompt(packet_path: Path) -> str:
    resume = load_resume()
    if resume:
        process = f"""
HUMAN SPECIATION RESUME MODE:
- Patrick already selected `{resume['decision']['selected']}` for fork `{resume['decision']['fork_id']}`.
- His recorded rationale is: {resume['decision']['rationale']}
- Selected mutation specification: {json.dumps(resume['selected_mutation'], ensure_ascii=False)}
- DO NOT diagnose a new wound and DO NOT generate a new mutation fork.
- Give the selected mutation directly to the Dramatist for implementation.
- Then run the required final six-Phantom implementation replay with all six independent roles and `background=false`.
- If and only if all six PASS, remove `story_room/resume_speciation.json` before exit so the successful implementation commit consumes the decision marker.
- If blocked or failed, leave `story_room/resume_speciation.json` in place so HermBeast retries this same selected mutation on the next scheduled run.
"""
    else:
        process = """
NORMAL EVOLUTION MODE:
- Diagnose the earliest structural wound from evidence.
- Have a separate Structural Editor create 2-4 genuinely different structural mutations using `background=false`.
- Have a separate Canon/Continuity Steward prosecute every mutation using `background=false`.
- Replay surviving mutations through the six logical walker identities.
- Have a separate Acumen Keeper compare survivors against the Story Genome using `background=false`.
- If inherited acumen uniquely decides the fork, select and implement it, then replay-test the implementation.
- If more than one genuinely different structurally valid future survives, DO NOT choose for Patrick. Write story_room/pending_speciation.json with compact A/B/C options in the form structural change -> story consequence -> price, then stop before implementation.
"""

    return f"""Run exactly one Voyd Story Room evolution cycle on THIS exact repository: {ROOT}.

IDENTITY / ISOLATION REQUIREMENTS:
- You are running under HermBeast only: `HERMES_HOME={HERMBEAST_HOME}`.
- Hermione (`{FORBIDDEN_HERMIONE_HOME}`) is a separate system and must never be read, written, invoked, delegated to, messaged, or used as a fallback for Voyd.
- Never use the KMS control bridge for Voyd.

Use the voyd-story-room skill as governing procedure. This supersedes the legacy numeric evolve.py promotion rubric.

Requirements:
- FIRST run `pwd` and verify it is exactly `{ROOT}`. If not, stop.
- For child context use the exact files `story_room/STORY_PHYSICS.md`, `story_room/genome.json`, `story_room/ROOM_PROTOCOL.md`, `story_room/walkers/<role>.md`, and the authoritative play packet `{packet_path}`; do not guess root-level aliases.
- Every Phantom Walker must judge `{packet_path}` first. Do not use browser/computer-use/execute_code to rediscover the playable story unless the packet is demonstrably inconsistent with the repository.
- Read the actual playable story, active story_room/genome.json, source-canon boundary, prior reports, and all six walker dossiers FROM `{ROOT}` only.
- Spawn the six Phantom Walkers as real Hermes delegated agents in ONE parallel batch with `background=false`; never background this batch.
{process}
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
- `blocked` means both available model routes or another external dependency prevented a trustworthy verdict; a single-provider outage alone is not sufficient if an approved fallback is available.
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
    hermes_home = Path(env["HERMES_HOME"]).resolve()
    if hermes_home != HERMBEAST_HOME.resolve():
        raise RuntimeError(f"Voyd Story Room requires HermBeast at {HERMBEAST_HOME}; got {hermes_home}")
    if hermes_home == FORBIDDEN_HERMIONE_HOME.resolve():
        raise RuntimeError("Voyd Story Room may never run under Hermione")
    delegate_tool = hermes_home / "hermes-agent" / "tools" / "delegate_tool.py"
    marker = "VOYD_FORCE_SYNC_DELEGATION=1: forcing delegate_task background=False"
    if not delegate_tool.exists() or marker not in delegate_tool.read_text(encoding="utf-8"):
        installer = ROOT / "scripts" / "install_hermes_story_room.py"
        raise RuntimeError(
            "HermBeast Story Room sync hook is not installed. Run: "
            f"{sys.executable} {installer} --hermes-home {hermes_home}"
        )


def read_status() -> dict | None:
    if not STATUS_PATH.exists():
        return None
    try:
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    required = {"status", "human_input_required", "final_replay", "summary"}
    if set(data) != required:
        return None
    return data


def write_blocked_status(summary: str) -> None:
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(
        json.dumps(
            {
                "status": "blocked",
                "human_input_required": False,
                "final_replay": "blocked",
                "summary": summary,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def clean_partial_attempt() -> None:
    subprocess.run(["git", "reset", "--hard", "HEAD"], cwd=ROOT, check=True)
    subprocess.run(["git", "clean", "-fd"], cwd=ROOT, check=True)


def resolve_hermes_executable(env: dict[str, str]) -> str:
    explicit_candidates = [
        HERMBEAST_HOME / "hermes-agent" / "venv" / "bin" / "hermes",
        HERMBEAST_HOME / "bin" / "hermes",
        Path("/home/patrick/.local/bin/hermes"),
    ]
    for candidate in explicit_candidates:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    found = shutil.which("hermes", path=env.get("PATH"))
    if found:
        return found
    raise RuntimeError("HermBeast executable 'hermes' was not found in the explicit HermBeast paths or PATH")


def run_hermes(prompt: str, env: dict[str, str], max_turns: int, *, provider: str | None = None, model: str | None = None) -> int:
    hermes_exe = resolve_hermes_executable(env)
    cmd = [
        hermes_exe, "chat", "-Q", "--in", str(ROOT),
        "--skills", SKILL, "--max-turns", str(max_turns),
        "--query-file", "-",
    ]
    if provider:
        cmd.extend(["--provider", provider])
    if model:
        cmd.extend(["--model", model])
    proc = subprocess.run(cmd, input=prompt, text=True, env=env)
    return proc.returncode


def run(max_turns: int) -> int:
    """Run exactly one HermBeast-native Story Room cycle.

    HermBeast is the ONLY model route for the Voyd Story Room. There is no
    silent local-Qwen fallback: if the HermBeast route cannot produce a
    trustworthy verdict, the cycle is written as BLOCKED (never silently
    substituted by a different model/identity). The supervisor then posts the
    block visibly so Patrick is never left guessing why nothing happened.
    """
    env = os.environ.copy()
    env["HERMES_HOME"] = str(HERMBEAST_HOME)
    env["VOYD_FORCE_SYNC_DELEGATION"] = "1"
    env["VIRTUAL_ENV"] = str(HERMBEAST_HOME / "hermes-agent" / "venv")
    env["PATH"] = HERMBEAST_PATH
    require_sync_hook(env)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.unlink(missing_ok=True)

    packet_path = build_packet()
    prompt = build_prompt(packet_path)
    primary_rc = run_hermes(prompt, env, max_turns)
    primary_status = read_status()

    if primary_rc == 0 and primary_status and primary_status["status"] != "blocked":
        return 0

    # The HermBeast model route did not return a usable verdict. Do NOT silently
    # substitute the local Qwen model: that would be a hidden identity/model
    # swap that Patrick cannot see. Write an explicit BLOCKED status and let the
    # supervisor announce it with a visible HermBeast post.
    reason = (
        "The HermBeast primary model route did not return a trustworthy Story "
        "Room verdict. No silent local-Qwen fallback was used; the cycle is "
        "blocked until the HermBeast model route is healthy."
    )
    if primary_status is None:
        reason = (
            f"The HermBeast primary model route exited {primary_rc} without writing "
            "a status file. No silent local-Qwen fallback was used; the cycle is "
            "blocked until the HermBeast model route is healthy."
        )
    print(f"[story-room] {reason}", flush=True)
    clean_partial_attempt()
    write_blocked_status(reason)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-turns", type=int, default=250)
    args = parser.parse_args(argv)
    started = datetime.now().isoformat()
    print(f"[story-room] starting {started}")
    return run(args.max_turns)


if __name__ == "__main__":
    raise SystemExit(main())
