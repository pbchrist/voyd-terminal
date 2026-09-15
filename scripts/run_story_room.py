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
LOCAL_PROVIDER = "local-qwen"  # Qwen 3.8 on 127.0.0.1:8082, defined in ~/.hermes/config.yaml
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


def build_prompt(packet_path: Path, baseline_ref: str = "HEAD") -> str:
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

STORY ROOM v3 SOURCE / STATE CONTRACT:
- Lore authority lives under `lore/`. Read `lore/README.md` first, then `lore/canon/CORE_LAWS.md` before planning any new fiction.
- `lore/canon/voyd_mythography.md` is immutable author-approved Voyd canon. `lore/universe/` is distilled universe reference. The complete novels registered in `lore/raw_sources.json` are evidence-only fallback for unresolved factual questions; NEVER imitate, paraphrase closely, or raid book prose for scene language.
- Generate from the universe's causal laws: parallel timestreams, one-way time, reweaving, downstream collateral effects, competing wills, intention/release, synchronicity/recruitment, and Voyd gravity. Do not keep recursively elaborating Terminal-invented metaphors merely because they appeared in prior scenes.
- `story_room/state/frontiers.json` is the structured causal projection of the live leaves. Read it before planning. Every accepted choice must leave a durable trace in facts, knowledge, relationships, spent resources, irreversible changes, causal chain, or open pressures. Update this file to exactly match the actual reachable leaves after every accepted mutation.
- `story_room/state/frontiers.json` is the only v3 causal-state authority; `story_room/state/canon_state.json` is retired and must never be required, guessed, or recreated.
- The protagonist's name is permanently `WITHHELD`. Structured state may establish role/want only after the fiction establishes them.
- NEW OR REWRITTEN SCENES: 250-450 prose words preferred; 550 prose words is a hard ceiling. A beat should be something a reader can consume before interaction fatigue sets in.
- BRANCH PERSISTENCE: autonomous cycles may NOT reduce the number of reachable live leaves. Never wire two prior live leaves directly into the same successor. Reconvergence is disabled for autonomous v3 until an explicit reviewed exception exists.
- Before declaring PASS, run `python3 scripts/validate_story_v3.py --base {baseline_ref}` and treat any ERROR as a failed cycle. Warnings are advisory; hard errors block publication.

STORY ROOM 2.0 JUDGMENT SYSTEM:
- The authoritative rubric is `story_room/STORYTELLING_JUDGMENT_RUBRIC.md`.
- Agent role contracts are under `story_room/agents/`; structured output contracts are under `story_room/schemas/`.
- The rubric is a diagnostic framework, never an optimization target and never an aggregate score.

Requirements:
- UNATTENDED TOOL SAFETY: this process runs under `hermes chat -Q` with nobody present to approve dangerous commands. NEVER use `execute_code`, shell heredocs, `python -c`, `python -e`, dynamically generated shell scripts, or any terminal action that requires interactive approval. Use file/read/search tools and simple non-interactive commands instead. Every delegated child receives this same restriction.
- QUALITY RETRY: a failed implementation replay is feedback, not permission to quit. Repair the selected mutation or try the next surviving mutation, rerun the independent Prose Editor, and replay again. Make up to THREE implementation/replay attempts inside this cycle before emitting `failed`. Never publish a failed attempt.
- FIRST run `pwd` and verify it is exactly `{ROOT}`. If not, stop.
- For child context use the exact files `story_room/STORY_PHYSICS.md`, `story_room/genome.json`, `story_room/ROOM_PROTOCOL.md`, `story_room/walkers/<role>.md`, and the authoritative play packet `{packet_path}`; do not guess root-level aliases.
- Every Phantom Walker must judge `{packet_path}` first. `reader_story` inside that packet is the PRIMARY playable fiction. The legacy `walks` material is continuity/history evidence, not the reader-facing target.
- Read `story/README.md`, all reachable `story/scenes/*.md`, and `story_room/frontier.json` as the authoritative living narrative surface. Read active story_room/genome.json, source-canon boundary, prior reports, and walker dossiers FROM `{ROOT}` only.
- Every accepted mutation must advance, deepen, differentiate, or repair the reader-facing fiction under `story/`; updating internal JSON alone is not a successful story evolution cycle.
- EVERY CYCLE MUST CHANGE THE FICTION, by ADVANCING or by HONING. The story is meant to be honed over time, not merely grown, so both are first-class outcomes and a cycle must end as exactly one of them:
  - ADVANCE: extend at least one active frontier listed in `story_room/frontier.json` with a NEW scene file under `story/scenes/` reachable by a choice link from its parent scene. Commit subject must begin `story-room: advance`.
  - HONE: no new scene, but a materially better one — rewrite, restructure, deepen or repair EXISTING scenes so the reader-facing fiction is measurably improved against the rubric and the genome. Commit subject must begin `story-room: hone`.
- A HONE cycle MUST still modify at least one file under `story/` (a scene, not only `story_room/` JSON). A cycle that edits no fiction has not honed anything, publishes nothing, and does not count as either outcome — keep working until one of the two is true.
- STALL GUARD: before choosing, run `git log --oneline -3 -- story/`. If the two most recent story commits are BOTH `hone`, this cycle MUST be an ADVANCE. The story may be polished for a night or two at a time; it may not stop moving.
- When you extend a frontier, replace that parent scene's ACTIVE FRONTIER block with a real reader-facing choice link into the new scene, and carry the unresolved pressure forward onto the new leaf. A frontier note is a placeholder for a scene that does not exist yet, never a substitute for one.
- NEVER write a choice link to a scene file you did not create in this cycle. A choice link is a promise the reader can click; if the target file does not exist, the publish workflow rejects the whole commit and the story does not reach the reader. The forward hook for a scene you have not written is an `## ◉ ACTIVE FRONTIER` block carrying the unresolved pressure, never a `### [label](file.md)` line. A scene ends with EITHER choice links OR a frontier block, never both: the reader parses everything after the frontier heading as the note, so a link under that heading is swallowed and the path reads as a dead end.
- Choose WHICH frontier to extend by what its unresolved pressure actually is, not by a fixed preference for depth. If the pressure is the NEXT BEAT of one path, extend that path with one scene. If the pressure is a genuine DILEMMA — two actions under pressure that a reader could each want, leading to states that differ in what the protagonist knows, owes, or has spent — then write BOTH successor scenes in this cycle and give the parent two choice links. A fork costs two scenes and is worth two scenes; it is not a widening to be rationed. Prefer the frontier that has gone longest without attention when the pressures are otherwise comparable.
- READER AGENCY IS A FIRST-CLASS OUTCOME. A reader must be able to feel that the story could have gone otherwise. A corridor of single-exit scenes fails this even when every scene is excellent. When you judge the fiction, judge whether the reader had a real choice, and treat "no reachable dilemma anywhere near the frontier" as a load-bearing diagnosis in its own right.
- THE PROTAGONIST IS A ROLE AND A WANT, NEVER A NAME. The reader-character is a cat of Faelspire, addressed as "you". Their NAME IS THE STORY'S WITHHELD OBJECT — it is filed by the ledger, it is what the record is about, and it is legible to the system and not to them. NEVER invent, reveal, or assign that name; it is immutable canon that it stays withheld. What is missing and must be established is everything else: what this cat DOES in the city, what they are carrying, and what they WANT badly enough to pay for. Independent cold readers have flagged that "you" has no role and no stake, so the story's biggest payoffs ("every one of them has your face") land on nothing. Fix that by grounding the role and the want in the fiction, not by naming them.
- Keep reader prose free of node IDs, lifecycle conditions, implementation jargon, score reports, and agent terminology. Choices must read as dramatic actions.
- On every accepted mutation, update `story_room/frontier.json` so canonical entry, canonical head, active frontier leaves, branch ancestry, and unresolved pressure remain current.
- PLATES: after the fiction is final and before you commit, run `python3 scripts/render_scene_image.py <scene>.md` for every scene you created or rewrote this cycle, and run `python3 scripts/render_scene_image.py --prune` if you deleted any scene. The plate draws the scene's INFLECTION MOMENT — the instant the state changes — never its scenery; pass `--moment "<one sentence naming the turn>"` when the scene's landing beat is not the turn. Art NEVER gates the story: if the renderer fails or ComfyUI is down, log it, commit the fiction anyway, and let a later cycle retry. Do not retry it more than once, and never let it change your verdict — a plate is never a reason to call a cycle failed.
- COLD WALK FIRST: spawn multiple real Hermes delegated leaf agents using `story_room/agents/cold_reader.md`. Cold readers MUST NOT read the rubric or diagnosis files before completing their walk. Validate each against `story_room/schemas/cold_walk.schema.json`.
- AFTER cold walks complete, spawn separate specialist delegated leaf judges using `story_room/agents/specialist_judges.md` plus `story_room/STORYTELLING_JUDGMENT_RUBRIC.md`. Specialists judge only their assigned domains and cite concrete evidence.
- Spawn a separate Governing Judge using `story_room/agents/governing_judge.md` to synthesize the cold walks and specialist reports. No aggregate score.
- The Governing Judge identifies the single load-bearing/high-leverage diagnosis. That diagnosis, not a low score, drives mutation.
- Mutation design, implementation, independent Prose Editor, and final replay follow `story_room/agents/mutation_and_replay.md`. The implementation agent may never be its own editor or final judge. The Prose Editor must use `story_room/agents/prose_editor.md`, preserve causal design, and may BLOCK publication for material prose failure.
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


def require_sync_hook(env: dict[str, str]) -> bool:
    """Verify or self-repair finite-session delegation before a Story Room run.

    Modern Hermes makes one-shot/stateless delegation synchronous natively. Older
    builds receive the narrow Voyd compatibility patch. A Hermes upgrade must not
    kill a scheduled story cycle merely because a historical patch disappeared.
    """
    hermes_home = Path(env["HERMES_HOME"]).resolve()
    if hermes_home != HERMBEAST_HOME.resolve():
        raise RuntimeError(f"Voyd Story Room requires HermBeast at {HERMBEAST_HOME}; got {hermes_home}")
    if hermes_home == FORBIDDEN_HERMIONE_HOME.resolve():
        raise RuntimeError("Voyd Story Room may never run under Hermione")

    installer = ROOT / "scripts" / "install_hermes_story_room.py"

    def ready() -> bool:
        check = subprocess.run(
            [sys.executable, str(installer), "--hermes-home", str(hermes_home), "--check"],
            cwd=ROOT, env=env, text=True, capture_output=True,
        )
        return check.returncode == 0

    if ready():
        return True

    try:
        repair = subprocess.run(
            [sys.executable, str(installer), "--hermes-home", str(hermes_home)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True,
        )
        if repair.stdout.strip():
            print(f"[story-room] {repair.stdout.strip()}", flush=True)
    except Exception as exc:
        print(
            f"[story-room] WARNING: delegation preflight could not self-repair ({exc}); "
            "continuing with Hermes finite-session fallback",
            flush=True,
        )
        env.pop("VOYD_FORCE_SYNC_DELEGATION", None)
        env["VOYD_SYNC_HOOK_DEGRADED"] = "1"
        return False

    if ready():
        return True

    print(
        "[story-room] WARNING: delegation repair completed but capability check still failed; "
        "continuing with explicit foreground-delegation instructions",
        flush=True,
    )
    env.pop("VOYD_FORCE_SYNC_DELEGATION", None)
    env["VOYD_SYNC_HOOK_DEGRADED"] = "1"
    return False

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


def note_route(route: str) -> None:
    """Stamp the verdict with the model route that produced it.

    read_status() enforces an exact four-key contract, so the provenance rides
    in the summary rather than in a new field. This is what keeps a fallback
    run honest: the story says which model wrote it.
    """
    data = read_status()
    if not data:
        return
    if not data["summary"].startswith("["):
        data["summary"] = f"[route: {route}] " + data["summary"]
        STATUS_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


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
    sync_hook_ok = require_sync_hook(env)
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.unlink(missing_ok=True)

    baseline_ref = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=True
    ).stdout.strip()
    packet_path = build_packet()
    prompt = build_prompt(packet_path, baseline_ref)
    if not sync_hook_ok:
        prompt += (
            "\n\nRUNTIME SAFETY OVERRIDE: the Hermes sync hook is unavailable. "
            "Do not launch background delegation. Every delegate_task call must set "
            "background=false and be awaited before continuing. Finish the cycle in this process.\n"
        )
    primary_rc = run_hermes(prompt, env, max_turns)
    primary_status = read_status()

    if primary_rc == 0 and primary_status and primary_status["status"] not in {"blocked"}:
        return 0

    # The primary route is unusable -- rate limit, outage, or no status written.
    # Retry once on the local Qwen 3.8 route. The standing rule forbids a
    # *silent* downgrade, not the local model itself: this attempt is announced
    # in the log and stamped into the verdict by note_route(), so a reader can
    # always tell which model wrote a given scene.
    print(
        f"[story-room] primary route unusable (rc={primary_rc}); retrying on {LOCAL_PROVIDER}",
        flush=True,
    )
    clean_partial_attempt()
    STATUS_PATH.unlink(missing_ok=True)
    fallback_rc = run_hermes(prompt, env, max_turns, provider=LOCAL_PROVIDER)
    fallback_status = read_status()
    if fallback_rc == 0 and fallback_status and fallback_status["status"] not in {"blocked"}:
        note_route(LOCAL_PROVIDER)
        return 0

    reason = (
        "Neither the HermBeast primary model route nor the local "
        f"{LOCAL_PROVIDER} route returned a trustworthy Story Room verdict; "
        "the cycle is blocked until a model route is healthy."
    )
    if primary_status is None and fallback_status is None:
        reason = (
            f"The primary route exited {primary_rc} and {LOCAL_PROVIDER} exited "
            f"{fallback_rc}; neither wrote a status file. The cycle is blocked "
            "until a model route is healthy."
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
