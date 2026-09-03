#!/usr/bin/env python3
"""Run one safe autonomous Story Room cycle, validate it, commit it, and push it."""
from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = os.environ.get("VOYD_AUTONOMOUS_BRANCH", "feat/story-engine-v2")
REMOTE = os.environ.get("VOYD_AUTONOMOUS_REMOTE", "origin")
HERMES_HOME = os.environ.get("HERMES_HOME", "/home/patrick/.hermes")
STATUS_PATH = ROOT / "story_room" / "reports" / "last_run_status.json"
PUBLIC_STATUS_PATH = ROOT / "story_room" / "autonomy_status.json"
PENDING_PATH = ROOT / "story_room" / "pending_speciation.json"
LOCK_PATH = ROOT / "logs" / ".autonomous_story_room.lock"
LOG_PATH = ROOT / "logs" / "autonomous_story_room.log"
PROTECTED_CANON = {
    "data/voyd_canon_mythography.md",
    "data/canon_events.json",
}


class AutonomyError(RuntimeError):
    pass


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(message: str) -> None:
    line = f"[{stamp()}] {message}"
    print(line, flush=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def visible_post(boundary: str, detail: str = "") -> None:
    """Send a VISIBLE HermBeast Telegram post at a Story Room boundary.

    This is the explicit, user-visible announcement channel. A failure to post
    is treated as an autonomy failure: the supervisor must never let a cycle
    start or end without a visible HermBeast post, and must never fall back to
    a hidden Qwen / log / status-JSON channel.
    """
    post_script = ROOT / "scripts" / "story_room_post.py"
    proc = subprocess.run(
        [sys.executable, str(post_script), "--boundary", boundary, "--detail", detail],
        cwd=ROOT,
        text=True,
        env=os.environ.copy(),
        capture_output=True,
    )
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "no output").strip()
        raise AutonomyError(f"visible HermBeast post ({boundary}) FAILED — cycle must not proceed silently: {err}")
    log(f"visible HermBeast post delivered: {boundary}")


def latest_reader_beats(since: str) -> str:
    """Return actual reader-facing fiction changed by this accepted cycle.

    Diffs the committed range (since..HEAD), not the working tree, so the
    Telegram beat can never describe content that failed to commit or push —
    the graph on the reader is built from the same committed scenes/frontier.
    """
    proc = subprocess.run(
        ["git", "diff", "--name-only", since, "HEAD", "--", "story/scenes", "story_room/frontier.json"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    scene_paths = []
    for rel in proc.stdout.splitlines():
        rel = rel.strip()
        if rel.startswith("story/scenes/") and rel.endswith(".md"):
            scene_paths.append(rel)

    if not scene_paths:
        try:
            frontier = json.loads((ROOT / "story_room" / "frontier.json").read_text(encoding="utf-8"))
            scene_paths = [x.get("path", "") for x in frontier.get("active_frontiers", []) if x.get("path")]
        except Exception:
            scene_paths = []

    lines = ["NEW STORY BEAT"]
    for rel in scene_paths[:3]:
        path = ROOT / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8").strip()
        title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), path.stem)
        body=[]
        for block in text.split("\n\n")[1:]:
            b=block.strip()
            if not b or b.startswith("#") or b.startswith("---") or b.startswith("**Branch") or b.startswith("**State"):
                continue
            if b.startswith("## Choose") or b.startswith("### ["):
                break
            body.append(b)
            if len(" ".join(body)) >= 650:
                break
        excerpt=" ".join(body)[:800].strip()
        lines.append(f"\n{title}\n{excerpt}")
    return "\n".join(lines).strip()


def write_public_status(status: str, summary: str, *, human_input_required: bool = False, final_replay: str = "not_applicable") -> None:
    PUBLIC_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_STATUS_PATH.write_text(
        json.dumps(
            {
                "timestamp_utc": stamp(),
                "status": status,
                "human_input_required": human_input_required,
                "final_replay": final_replay,
                "summary": summary,
            },
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    if check and proc.returncode != 0:
        detail = ""
        if capture:
            detail = f"\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        raise AutonomyError(f"command failed ({proc.returncode}): {' '.join(cmd)}{detail}")
    return proc


def git(*args: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], check=check, capture=capture)


def acquire_lock():
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    handle = LOCK_PATH.open("w")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def current_branch() -> str:
    return git("branch", "--show-current").stdout.strip()


def status_paths() -> set[str]:
    changed = set(filter(None, git("diff", "--name-only", "HEAD").stdout.splitlines()))
    untracked = set(filter(None, git("ls-files", "--others", "--exclude-standard").stdout.splitlines()))
    return changed | untracked


def ensure_clean_and_synced() -> None:
    branch = current_branch()
    if branch != BRANCH:
        raise AutonomyError(f"refusing to run on branch {branch!r}; expected {BRANCH!r}")
    dirty = git("status", "--porcelain", "--untracked-files=all").stdout.strip()
    if dirty:
        raise AutonomyError(f"refusing to start from a dirty worktree:\n{dirty}")

    git("fetch", REMOTE, BRANCH)
    remote_ref = f"{REMOTE}/{BRANCH}"
    local_sha = git("rev-parse", "HEAD").stdout.strip()
    remote_sha = git("rev-parse", remote_ref).stdout.strip()
    if local_sha == remote_sha:
        return

    local_is_ancestor = git("merge-base", "--is-ancestor", local_sha, remote_sha, check=False).returncode == 0
    remote_is_ancestor = git("merge-base", "--is-ancestor", remote_sha, local_sha, check=False).returncode == 0
    if local_is_ancestor:
        log(f"fast-forwarding local branch to {remote_sha[:12]}")
        git("merge", "--ff-only", remote_ref, capture=False)
        return
    if remote_is_ancestor:
        log("local branch is ahead of GitHub; pushing pending local commits before next cycle")
        git("push", REMOTE, f"HEAD:{BRANCH}", capture=False)
        return
    raise AutonomyError("local and remote branches diverged; human review required")


def discard_incomplete_run() -> None:
    log("discarding incomplete autonomous story changes; ignored run reports are preserved")
    git("reset", "--hard", "HEAD", capture=False)
    git("clean", "-fd", capture=False)


def load_status() -> dict:
    if not STATUS_PATH.exists():
        raise AutonomyError("Story Room exited without writing last_run_status.json")
    try:
        data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AutonomyError(f"invalid Story Room status JSON: {exc}") from exc
    required = {"status", "human_input_required", "final_replay", "summary"}
    if set(data) != required:
        raise AutonomyError(f"unexpected Story Room status schema: {sorted(data)}")
    return data


def verify_canon_untouched() -> None:
    changed = status_paths()
    touched = sorted(PROTECTED_CANON & changed)
    if touched:
        raise AutonomyError(f"immutable source canon was modified: {touched}")


def validate_json() -> None:
    candidates = list((ROOT / "data").glob("*.json"))
    candidates += list((ROOT / "frontend").glob("*.json"))
    candidates += list((ROOT / "frontend" / "data").glob("*.json"))
    candidates.append(ROOT / "story_room" / "genome.json")
    for path in candidates:
        if path.exists():
            json.loads(path.read_text(encoding="utf-8"))


def validate_passed_run() -> None:
    verify_canon_untouched()
    run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], capture=False)
    validate_json()
    git("diff", "--check")


def commit_and_push(message: str, allowed_only: set[str] | None = None) -> bool:
    changed = status_paths()
    if allowed_only is not None:
        unexpected = sorted(changed - allowed_only)
        if unexpected:
            raise AutonomyError("unexpected files for constrained commit: " + ", ".join(unexpected))
    if not changed:
        log("cycle produced no durable changes; no commit needed")
        return False

    touched = sorted(PROTECTED_CANON & changed)
    if touched:
        raise AutonomyError(f"refusing to stage immutable canon: {touched}")

    git("add", "-A", capture=False)
    staged = set(filter(None, git("diff", "--cached", "--name-only").stdout.splitlines()))
    if PROTECTED_CANON & staged:
        raise AutonomyError("immutable canon reached the Git index; refusing commit")
    if allowed_only is not None and staged - allowed_only:
        raise AutonomyError(f"unexpected staged files: {sorted(staged - allowed_only)}")
    if not staged:
        log("nothing staged; no commit needed")
        return False

    git("commit", "-m", message, capture=False)
    git("push", REMOTE, f"HEAD:{BRANCH}", capture=False)
    log(f"pushed autonomous commit: {git('rev-parse', '--short', 'HEAD').stdout.strip()}")
    return True


def commit_status_only(message: str) -> None:
    commit_and_push(message, allowed_only={"story_room/autonomy_status.json"})


def one_cycle() -> int:
    ensure_clean_and_synced()
    if PENDING_PATH.exists():
        write_public_status("pending_speciation", "Story Room is waiting for Patrick's artistic decision.", human_input_required=True)
        commit_status_only(f"story-room: status pending speciation {stamp()}")
        log("paused: story_room/pending_speciation.json requires Patrick's decision")
        return 0

    before = git("rev-parse", "HEAD").stdout.strip()
    log(f"starting autonomous Story Room cycle from {before[:12]}")
    visible_post("start", f"Starting autonomous Story Room cycle from {before[:12]}. Running under HermBeast only (HERMES_HOME={HERMES_HOME}).")
    proc = run([sys.executable, str(ROOT / "scripts" / "run_story_room.py")], check=False, capture=False)
    if proc.returncode != 0:
        discard_incomplete_run()
        write_public_status("failed", f"Story Room process exited {proc.returncode}; no story mutation was accepted.", final_replay="failed")
        visible_post("failed", f"Story Room process exited {proc.returncode}; no story mutation was accepted.")
        commit_status_only(f"story-room: record failed cycle {stamp()}")
        return 0

    preserve_on_error = False
    try:
        result = load_status()
        status = result["status"]
        log(f"Story Room verdict: {status}: {result['summary']}")

        if status == "pending_speciation":
            preserve_on_error = True
            if not result["human_input_required"] or not PENDING_PATH.exists():
                raise AutonomyError("pending_speciation verdict is missing its required decision packet")
            write_public_status(status, result["summary"], human_input_required=True, final_replay=result["final_replay"])
            visible_post("decision", f"Story Room stopped for Patrick's speciation decision. {result['summary']}")
            commit_and_push(
                f"story-room: request Patrick speciation decision {stamp()}",
                allowed_only={"story_room/pending_speciation.json", "story_room/autonomy_status.json"},
            )
            log("autonomy paused at a genuine artistic fork")
            return 0

        if status in {"blocked", "failed"}:
            summary = result["summary"]
            replay = result["final_replay"]
            discard_incomplete_run()
            write_public_status(status, summary, human_input_required=result["human_input_required"], final_replay=replay)
            visible_post(status, f"Story Room {status}. {summary}")
            commit_status_only(f"story-room: record {status} cycle {stamp()}")
            log(f"no story commit: {status} gate did not pass; status was pushed")
            return 0

        if status != "passed":
            raise AutonomyError(f"unknown Story Room verdict: {status!r}")
        if result["human_input_required"]:
            raise AutonomyError("passed verdict cannot simultaneously require human input")
        if result["final_replay"] != "passed":
            raise AutonomyError("passed verdict without a passed final six-Phantom replay")

        write_public_status("passed", result["summary"], final_replay="passed")
        run([sys.executable, str(ROOT / "scripts" / "render_story_md.py")], check=True, capture=False)
        validate_passed_run()
        pushed = commit_and_push(f"story-room: autonomous evolution {stamp()}")
        if pushed:
            visible_post("passed", f"Story Room PASSED with a clean final six-Phantom replay. {result['summary']}\n\n{latest_reader_beats(before)}")
        else:
            visible_post("passed", f"Story Room PASSED with a clean final six-Phantom replay, but produced no committed change. {result['summary']}")
        return 0
    except Exception as exc:
        if preserve_on_error:
            log("preserving speciation worktree for human inspection")
            raise
        discard_incomplete_run()
        write_public_status("failed", f"Autonomy supervisor error: {exc}", final_replay="failed")
        visible_post("failed", f"Story Room supervisor error: {exc}")
        commit_status_only(f"story-room: record supervisor failure {stamp()}")
        return 0


def main() -> int:
    lock = acquire_lock()
    if lock is None:
        log("another autonomous Story Room cycle is already running; exiting")
        return 0
    try:
        return one_cycle()
    except Exception as exc:
        log(f"ERROR: {exc}")
        return 1
    finally:
        lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
