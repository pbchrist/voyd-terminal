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
LEGACY RECORDED DECISION RESUME MODE:
- Patrick already selected `{resume['decision']['selected']}` for fork `{resume['decision']['fork_id']}`.
- His recorded rationale is: {resume['decision']['rationale']}
- Selected mutation specification: {json.dumps(resume['selected_mutation'], ensure_ascii=False)}
- DO NOT diagnose a new wound and DO NOT generate a new mutation fork.
- Give the selected mutation directly to the Dramatist for implementation.
- Then run the required final independent implementation replay.
- If and only if replay passes, remove `story_room/resume_speciation.json` before exit so the successful implementation commit consumes the legacy decision marker.
- If blocked or failed, leave `story_room/resume_speciation.json` in place so HermBeast retries this same selected mutation on the next scheduled run.
"""
    else:
        process = """
NORMAL EVOLUTION MODE — AUTONOMOUS:
- Run cold reader/player walks before exposing those agents to the rubric.
- Run specialist rubric judges over the completed walk evidence.
- Run a separate Governing Judge to diagnose the earliest load-bearing or highest-leverage wound from evidence.
- Have a separate Structural Editor create 2-4 genuinely different structural mutations using `background=false`.
- Have a separate Canon/Continuity Steward prosecute every mutation using `background=false`.
- Replay surviving mutations through independent delegated replay walkers, including changed paths, neighboring paths, one unaffected control path, downstream reconvergences, and affected endings.
- Have a separate Acumen Keeper compare survivors against the Story Genome using `background=false`.
- If one surviving mutation clearly dominates, select it as canonical, implement it, and replay-test the implementation.
- If multiple genuinely different structurally valid futures survive, DO NOT stop for Patrick and DO NOT create `pending_speciation.json`. Preserve the meaningful survivors as active reader-facing branches where structurally coherent; choose one canonical head using the Governing Judge, Acumen Keeper, Story Genome, causal leverage, and replay evidence; implement and replay-test the accepted branch set.
- Ambiguous taste is branch material, not a reason to stop the organism.
"""

    return f"""Run exactly one Voyd Story Room evolution cycle on THIS exact repository: {ROOT}.

IDENTITY / ISOLATION REQUIREMENTS:
- You are running under HermBeast only: `HERMES_HOME={HERMBEAST_HOME}`.
- Hermione (`{FORBIDDEN_HERMIONE_HOME}`) is a separate system and must never be read, written, invoked, delegated to, messaged, or used as a fallback for Voyd.
- Never use the KMS control bridge for Voyd.

Use the voyd-story-room skill as governing procedure. This supersedes the legacy numeric evolve.py promotion rubric.

STORY ROOM 2.0 JUDGMENT SYSTEM:
- The authoritative rubric is `story_room/STORYTELLING_JUDGMENT_RUBRIC.md`.
- Agent role contracts are under `story_room/agents/`; structured output contracts are under `story_room/schemas/`.
- The rubric is a diagnostic framework, never an optimization target and never an aggregate score.

Requirements:
- FIRST run `pwd` and verify it is exactly `{ROOT}`. If not, stop.
- For child context use the exact files `story_room/STORY_PHYSICS.md`, `story_room/genome.json`, `story_room/ROOM_PROTOCOL.md`, `story_room/walkers/<role>.md`, and the authoritative play packet `{packet_path}`; do not guess root-level aliases.
- Every Phantom Walker must judge `{packet_path}` first. `reader_story` inside that packet is the PRIMARY playable fiction. The legacy `walks` material is continuity/history evidence, not the reader-facing target.
- Read `story/README.md`, all reachable `story/scenes/*.md`, and `story_room/frontier.json` as the authoritative living narrative surface. Read active story_room/genome.json, source-canon boundary, prior reports, and walker dossiers FROM `{ROOT}` only.
- Every accepted mutation must advance, deepen, differentiate, or repair the reader-facing fiction under `story/`; updating internal JSON alone is not a successful story evolution cycle.
- Keep reader prose free of node IDs, lifecycle conditions, implementation jargon, score reports, and agent terminology. Choices must read as dramatic actions.
- On every accepted mutation, update `story_room/frontier.json` so canonical entry, canonical head, active frontier leaves, branch ancestry, and unresolved pressure remain current.
- COLD WALK FIRST: spawn multiple real Hermes delegated leaf agents using `story_room/agents/cold_reader.md`. Cold readers MUST NOT read the rubric or diagnosis files before completing their walk. Validate each against `story_room/schemas/cold_walk.schema.json`.
- AFTER cold walks complete, spawn separate specialist delegated leaf judges using `story_room/agents/specialist_judges.md` plus `story_room/STORYTELLING_JUDGMENT_RUBRIC.md`. Specialists judge only their assigned domains and cite concrete evidence.
- Spawn a separate Governing Judge using `story_room/agents/governing_judge.md` to synthesize the cold walks and specialist reports. No aggregate score.
- The Governing Judge identifies the single load-bearing/high-leverage diagnosis. That diagnosis, not a low score, drives mutation.
- Mutation design, implementation, and independent replay follow `story_room/agents/mutation_and_replay.md`. The implementation agent may never be its own final judge.
- Use real Hermes `delegate_task` subagents for every specialist role. Keep roles isolated and persist their outputs under `story_room/reports/<cycle>/`.
- NEVER require Patrick to choose between surviving story futures during a scheduled cycle. Keep viable divergence as branches and keep writing.
{process}
- Never edit source/book canon.
- Never use numeric story-quality averages or tension_delta as proof of drama.
- Never use the legacy forced-archetype Phantom Walker script as a substitute for delegated walkers.
- Do not merge to main or read/write another worktree. Never fall back to `/home/patrick/voyd-terminal`.

Before you exit, ALWAYS write `{STATUS_PATH}` as valid JSON with exactly these fields:
{{
  "status": "passed|blocked|failed",
  "human_input_required": false,
  "final_replay": "passed|blocked|failed",
  "summary": "one concise factual sentence"
}}
Rules for that status file:
- `passed` is allowed ONLY after implemented reader-facing fiction completes the required independent final replay and passes.
- `blocked` means an external dependency prevented a trustworthy verdict or implementation; do not substitute a hidden model identity.
- `failed` means the cycle itself failed mechanically or violated a required invariant.
- `pending_speciation` is forbidden in autonomous scheduled mode.
- `human_input_required` must be false in autonomous scheduled mode.
- Never claim `passed` because tests alone passed. Independent final replay is mandatory.

Persist reports and artifacts under story_room/. End with a concise factual summary. Do not require Patrick input to finish an artistic fork.
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
    """Run exactly one HermBeast-native Story Room cycle."""
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

    if primary_rc == 0 and primary_status and primary_status["status"] not in {"blocked"}:
        return 0

    reason = (
        "The HermBeast primary model route did not return a trustworthy Story Room verdict. "
        "No silent local-Qwen fallback was used; the cycle is blocked until the HermBeast model route is healthy."
    )
    if primary_status is None:
        reason = (
            f"The HermBeast primary model route exited {primary_rc} without writing a status file. "
            "No silent local-Qwen fallback was used; the cycle is blocked until the HermBeast model route is healthy."
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
