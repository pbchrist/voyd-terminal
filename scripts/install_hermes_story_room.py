#!/usr/bin/env python3
"""Install the narrow Hermes runtime hook required by finite Story Room runs."""
from __future__ import annotations

import argparse
import os
import shutil
from datetime import datetime
from pathlib import Path

MARKER = 'VOYD_FORCE_SYNC_DELEGATION=1: forcing delegate_task background=False'
ANCHOR = '''    background = is_truthy_value(background, default=False) if background is not None else False

    # Depth limit — configurable via delegation.max_spawn_depth,
'''
REPLACEMENT = '''    background = is_truthy_value(background, default=False) if background is not None else False

    # Voyd Story Room runs are finite one-shot orchestration sessions.
    # The project runner opts into synchronous fan-out/fan-in at runtime.
    # Ordinary Hermes chats keep normal background delegation.
    if os.environ.get("VOYD_FORCE_SYNC_DELEGATION") == "1" and background:
        logger.info("VOYD_FORCE_SYNC_DELEGATION=1: forcing delegate_task background=False")
        background = False

    # Depth limit — configurable via delegation.max_spawn_depth,
'''


def install(hermes_home: Path) -> str:
    target = hermes_home / "hermes-agent" / "tools" / "delegate_tool.py"
    if not target.exists():
        raise FileNotFoundError(f"Hermes delegate tool not found: {target}")
    text = target.read_text(encoding="utf-8")
    if MARKER in text:
        return f"already installed: {target}"
    if ANCHOR not in text:
        raise RuntimeError("Hermes delegate_tool.py changed; refusing to patch an unknown version")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target.with_name(target.name + f".bak-voyd-story-room-{stamp}")
    shutil.copy2(target, backup)
    target.write_text(text.replace(ANCHOR, REPLACEMENT, 1), encoding="utf-8")
    return f"installed: {target}\nbackup: {backup}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hermes-home",
        type=Path,
        default=Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")),
        help="Hermes home to patch; defaults to HERMES_HOME or ~/.hermes",
    )
    args = parser.parse_args()
    print(install(args.hermes_home.expanduser().resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
