#!/usr/bin/env python3
"""Publication guards for Story Room v3.

Checks only hard mechanical contracts. Artistic judgment remains with Story Room.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = ROOT / "story" / "scenes"
FRONTIER = ROOT / "story_room" / "frontier.json"
LINK = re.compile(r"\]\(([^)]+\.md)\)")
WORD = re.compile(r"\b[\w’'-]+\b")
MAX_CHANGED_SCENE_WORDS = 550
PREFERRED_MIN = 250
PREFERRED_MAX = 450


def scene_graph(root: Path = SCENES) -> dict[str, list[str]]:
    return {p.name: LINK.findall(p.read_text(encoding="utf-8")) for p in root.glob("*.md")}


def reachable(graph: dict[str, list[str]], entry: str) -> set[str]:
    seen: set[str] = set()
    stack = [entry]
    while stack:
        node = stack.pop()
        if node in seen or node not in graph:
            continue
        seen.add(node)
        stack.extend(graph[node])
    return seen


def prose_word_count(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    prose = text.split("---", 1)[0]
    prose = re.sub(r"^#+\s+.*$", "", prose, flags=re.M)
    return len(WORD.findall(prose))


def git_changed_scene_names(base: str = "HEAD") -> set[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", base, "--", "story/scenes"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    names = {Path(line.strip()).name for line in proc.stdout.splitlines() if line.strip().endswith(".md")}
    proc = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "story/scenes"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    names.update(Path(line.strip()).name for line in proc.stdout.splitlines() if line.strip().endswith(".md"))
    return names


def validate_changed_lengths(base: str = "HEAD") -> list[str]:
    errors: list[str] = []
    for name in sorted(git_changed_scene_names(base)):
        path = SCENES / name
        if not path.exists():
            continue
        words = prose_word_count(path)
        if words > MAX_CHANGED_SCENE_WORDS:
            errors.append(f"{name}: {words} prose words; changed scenes must be <= {MAX_CHANGED_SCENE_WORDS}")
    return errors


def frontier_errors(graph: dict[str, list[str]]) -> list[str]:
    data = json.loads(FRONTIER.read_text(encoding="utf-8"))
    entry = Path(data.get("canonical_entry", "")).name
    live = reachable(graph, entry)
    leaves = {n for n in live if not graph.get(n)}
    declared = {
        Path(item.get("path", "")).name
        for item in data.get("active_frontiers", [])
    }
    errors: list[str] = []
    if leaves != declared:
        missing = sorted(leaves - declared)
        stale = sorted(declared - leaves)
        errors.append(
            f"frontier ledger drift: missing={missing or '[]'} stale={stale or '[]'}"
        )
    return errors


def graph_at(ref: str) -> dict[str, list[str]]:
    names = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref, "story/scenes"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    ).stdout.splitlines()
    graph: dict[str, list[str]] = {}
    for rel in names:
        if not rel.endswith(".md"):
            continue
        body = subprocess.run(
            ["git", "show", f"{ref}:{rel}"], cwd=ROOT,
            text=True, capture_output=True, check=True,
        ).stdout
        graph[Path(rel).name] = LINK.findall(body)
    return graph

def branch_collapse_errors(current: dict[str, list[str]], base: str) -> list[str]:
    previous = graph_at(base)
    previous_entry = "000-the-fourth-bell.md"
    old_live = reachable(previous, previous_entry)
    old_leaves = sorted(n for n in old_live if not previous.get(n))
    target_to_leaves: dict[str, list[str]] = {}
    for leaf in old_leaves:
        links = current.get(leaf, [])
        if len(links) != 1:
            continue
        target_to_leaves.setdefault(links[0], []).append(leaf)
    return [
        "branch collapse: prior live leaves " + ", ".join(sorted(leaves))
        + f" now all point directly to {target}"
        for target, leaves in sorted(target_to_leaves.items())
        if len(leaves) > 1
    ]


def preferred_length_warnings(base: str = "HEAD") -> list[str]:
    warnings: list[str] = []
    for name in sorted(git_changed_scene_names(base)):
        path = SCENES / name
        if not path.exists():
            continue
        words = prose_word_count(path)
        if words < PREFERRED_MIN or words > PREFERRED_MAX:
            warnings.append(
                f"{name}: {words} prose words; preferred range is "
                f"{PREFERRED_MIN}-{PREFERRED_MAX}"
            )
    return warnings


def validate(base: str = "HEAD") -> tuple[list[str], list[str]]:
    graph = scene_graph()
    errors = validate_changed_lengths(base)
    errors.extend(frontier_errors(graph))
    errors.extend(branch_collapse_errors(graph, base))
    return errors, preferred_length_warnings(base)

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Story Room v3 publication contracts")
    parser.add_argument("--base", default="HEAD", help="git ref used as the pre-change baseline")
    args = parser.parse_args()
    errors, warnings = validate(args.base)
    for warning in warnings:
        print(f"WARN: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"FAIL: {len(errors)} hard contract violation(s)")
        return 1
    print("PASS: Story Room v3 hard contracts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
