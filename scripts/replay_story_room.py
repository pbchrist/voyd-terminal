#!/usr/bin/env python3
"""Run only the final six-Phantom implementation replay gate."""
from __future__ import annotations

import argparse
import os
import subprocess
from datetime import datetime
from pathlib import Path

from run_story_room import ROOT, SKILL, build_packet, require_sync_hook


def build_prompt(packet_path: Path, report_dir: Path) -> str:
    return f"""Run ONLY the final implementation replay gate for the Voyd Story Room.

Repository authority: {ROOT}
Authoritative model-free play packet: {packet_path}
Report directory: {report_dir}

Requirements:
- Verify `pwd` is exactly `{ROOT}`.
- Read story_room/STORY_PHYSICS.md, story_room/ROOM_PROTOCOL.md, story_room/genome.json, the selected implemented story, tests/test_four_binding_contracts.py, and the authoritative packet.
- Spawn exactly six real Phantom Walker agents in one parallel `delegate_task(..., background=false)` batch: Transformation Architect, Scene Mechanic, Dialogue Combatant, Causality & Continuity Prosecutor, Interactive Drama Adversary, Brutal Audience.
- Give each its exact dossier under story_room/walkers/ and the SAME authoritative packet.
- Read-only review. Do not edit story, tests, canon, or runtime.
- Each walker must verify the original false-choice wound is gone, the selected Four Binding Contracts species remains intact, the /api/chat proxy handoff preserves contract causality, and no earlier/worse wound was introduced.
- No numeric quality averages. Each returns PASS or FAIL with first_failure and evidence.
- Persist six reports plus aggregate.json under `{report_dir}`.
- Overall PASS requires all six PASS. Do not fabricate a verdict if a provider or tool failure prevents review.
- Do not use browser/computer-use/execute-code discovery unless the supplied packet demonstrably contradicts the repository.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--max-turns", type=int, default=120)
    args = parser.parse_args()
    env = os.environ.copy()
    env.setdefault("HERMES_HOME", str(Path.home() / ".hermes"))
    env["VOYD_FORCE_SYNC_DELEGATION"] = "1"
    require_sync_hook(env)
    packet = build_packet()
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    report_dir = ROOT / "story_room" / "reports" / f"implementation_replay_{stamp}"
    cmd = [
        "hermes", "chat", "-Q", "--in", str(ROOT), "--skills", SKILL,
        "--max-turns", str(args.max_turns), "--query-file", "-",
    ]
    proc = subprocess.run(cmd, input=build_prompt(packet, report_dir), text=True, env=env)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
