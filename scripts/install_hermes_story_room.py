#!/usr/bin/env python3
"""Verify or repair synchronous delegation for finite Voyd Story Room runs.

Modern Hermes natively keeps delegation inline for finite ``chat -Q`` sessions.
Older builds receive a narrow compatibility hook. Installation is feature-
detected, backed up, syntax-checked, and rolled back on any patch failure.
"""
from __future__ import annotations

import argparse
import os
import py_compile
import shutil
from datetime import datetime
from pathlib import Path

MARKER = "VOYD_FORCE_SYNC_DELEGATION=1: forcing delegate_task background=False"
NATIVE_ONESHOT_MARKER = "declare_stateless_channel()"
NATIVE_DISPATCH_MARKER = "finite chat using -Q"
BACKGROUND_LINE = "    background = is_truthy_value(background, default=False) if background is not None else False\n"
# Backward-compatible fixture/API retained for older tests and Hermes layouts.
ANCHOR = (
    "import logging\n\n"
    "def delegate_task(background=None):\n"
    + BACKGROUND_LINE
    + "\n    # Depth limit — configurable via delegation.max_spawn_depth,\n"
)
HOOK = (
    "\n    # Voyd finite Story Room compatibility hook.\n"
    "    if os.environ.get(\"VOYD_FORCE_SYNC_DELEGATION\") == \"1\" and background:\n"
    "        logger.info(\"VOYD_FORCE_SYNC_DELEGATION=1: forcing delegate_task background=False\")\n"
    "        background = False\n"
)


def native_sync_supported(hermes_home: Path) -> bool:
    agent = hermes_home / "hermes-agent"
    oneshot = agent / "hermes_cli" / "oneshot.py"
    dispatch = agent / "tools" / "delegate_tool_dispatch.py"
    if not oneshot.exists() or not dispatch.exists():
        return False
    return (
        NATIVE_ONESHOT_MARKER in oneshot.read_text(encoding="utf-8")
        and NATIVE_DISPATCH_MARKER in dispatch.read_text(encoding="utf-8")
    )


def legacy_patch_installed(hermes_home: Path) -> bool:
    target = hermes_home / "hermes-agent" / "tools" / "delegate_tool.py"
    return target.exists() and MARKER in target.read_text(encoding="utf-8")


def is_ready(hermes_home: Path) -> bool:
    return native_sync_supported(hermes_home) or legacy_patch_installed(hermes_home)


def install(hermes_home: Path) -> str:
    if native_sync_supported(hermes_home):
        return "native finite-session synchronous delegation supported; no Hermes patch required"

    target = hermes_home / "hermes-agent" / "tools" / "delegate_tool.py"
    if not target.exists():
        raise FileNotFoundError(f"Hermes delegate tool not found: {target}")
    original = target.read_text(encoding="utf-8")
    if MARKER in original:
        return f"legacy compatibility hook already installed: {target}"
    if original.count(BACKGROUND_LINE) != 1:
        raise RuntimeError("Hermes delegation layout has no unique background assignment; refusing unsafe patch")

    patched = original
    if "import os\n" not in patched:
        if "import logging\n" not in patched:
            raise RuntimeError("Hermes import layout changed; refusing unsafe patch")
        patched = patched.replace("import logging\n", "import logging\nimport os\n", 1)
    patched = patched.replace(BACKGROUND_LINE, BACKGROUND_LINE + HOOK, 1)

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = target.with_name(target.name + f".bak-voyd-story-room-{stamp}")
    shutil.copy2(target, backup)
    try:
        target.write_text(patched, encoding="utf-8")
        py_compile.compile(str(target), doraise=True)
        if not legacy_patch_installed(hermes_home):
            raise RuntimeError("compatibility hook marker missing after patch")
    except Exception:
        shutil.copy2(backup, target)
        raise
    return f"installed legacy compatibility hook: {target}\nbackup: {backup}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hermes-home",
        type=Path,
        default=Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes")),
        help="Hermes home to verify/repair; defaults to HERMES_HOME or ~/.hermes",
    )
    parser.add_argument("--check", action="store_true", help="verify capability without changing Hermes")
    args = parser.parse_args()
    home = args.hermes_home.expanduser().resolve()
    if args.check:
        print("ready" if is_ready(home) else "not ready")
        return 0 if is_ready(home) else 1
    print(install(home))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
