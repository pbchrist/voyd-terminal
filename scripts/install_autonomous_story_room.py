#!/usr/bin/env python3
"""Install and start the autonomous Voyd Story Room user timer."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT_DIR = ROOT / "systemd"
TARGET_DIR = Path.home() / ".config" / "systemd" / "user"
UNITS = ("voyd-story-room.service", "voyd-story-room.timer")


def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(list(args), text=True, check=check)


def install(run_now: bool) -> int:
    expected = "feat/story-engine-v2"
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip()
    if branch != expected:
        raise RuntimeError(f"refusing to install from branch {branch!r}; expected {expected!r}")

    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=all"], cwd=ROOT, text=True
    ).strip()
    if dirty:
        raise RuntimeError("refusing to install from a dirty worktree")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for name in UNITS:
        src = UNIT_DIR / name
        if not src.exists():
            raise FileNotFoundError(src)
        shutil.copy2(src, TARGET_DIR / name)
        print(f"installed {TARGET_DIR / name}")

    run("systemctl", "--user", "daemon-reload")
    run("systemctl", "--user", "enable", "--now", "voyd-story-room.timer")
    print("timer enabled")
    run("systemctl", "--user", "status", "voyd-story-room.timer", "--no-pager", check=False)

    if run_now:
        run("systemctl", "--user", "start", "--no-block", "voyd-story-room.service")
        print("first autonomous Story Room cycle launched")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--no-run-now",
        action="store_true",
        help="install/enable the timer without launching the first cycle immediately",
    )
    args = parser.parse_args()
    return install(run_now=not args.no_run_now)


if __name__ == "__main__":
    raise SystemExit(main())
