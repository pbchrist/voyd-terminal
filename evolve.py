#!/usr/bin/env python3
"""Run one Narrative Evolution Directives cycle for the Voyd Terminal.

The cycle is intentionally data-driven:
- read story_map.json, rubric.json, canon_events.json, act1_nodes.json
- detect structural problems before generation
- select one unused canon event matching the current story need
- generate one canon-rooted Voyd node from the event's voyd_pov seed
- score on dialectic_function, tension_advancement, branch_choke_logic
- auto-promote >= 24, kill < 18, send 18-23 to Telegram for Patrick
"""

from __future__ import annotations

import fcntl
import json
import os
import re
import subprocess
import sys
import textwrap
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
DATA_DIR = REPO_ROOT / "data"
ACT1_NODES_PATH = DATA_DIR / "act1_nodes.json"
STORY_MAP_PATH = DATA_DIR / "story_map.json"
RUBRIC_PATH = DATA_DIR / "rubric.json"
CANON_EVENTS_PATH = DATA_DIR / "canon_events.json"
BUILD_SCRIPT = REPO_ROOT / "build_frontend.py"
LOG_PATH = REPO_ROOT / "logs" / "evolve.log"
LOCK_PATH = REPO_ROOT / "logs" / ".evolve.lock"
HEAL_LOG_PATH = REPO_ROOT / "logs" / "heal_log.json"
AUTO_PROMOTE_DEFAULT = 24
AUTO_KILL_DEFAULT = 18
PHANTOM_UNIQUENESS_FLOOR = 7.0
HEAL_AUTO_THRESHOLD = 26
IMMUNE_WALK_GATE = 20
MINE_WHEN_UNUSED_BELOW = 2
SCORE_AXES = ("dialectic_function", "tension_advancement", "branch_choke_logic")

QWEN_BASE_URL = "http://localhost:8081/v1"
QWEN_MODEL = "Qwen3.6-27B-Q6_K"


def log(message: str) -> None:
    line = f"[{datetime.now().isoformat()}] {message}"
    if sys.stdout.isatty():
        print(line)  # cron redirects stdout into the log file; printing there would duplicate every line
    if os.environ.get("VOYD_TEST"):
        return  # keep test runs out of the production log
    LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    env_path = path or Path(os.path.expanduser("~/.hermes/.env"))
    values: dict[str, str] = {}
    if not env_path.exists():
        return values
    for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


# Inject .env into os.environ immediately so cron jobs pick up credentials.
for _k, _v in load_dotenv().items():
    os.environ.setdefault(_k, _v)


def qwen_chat(messages: list, max_tokens: int = 300, temperature: float = 0.9) -> str:
    """Call local Qwen chat completions endpoint."""
    payload = {
        "model": QWEN_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        f"{QWEN_BASE_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


def load_state(root: Path = REPO_ROOT) -> dict[str, Any]:
    return {
        "root": root,
        "story_map": read_json(root / "data/story_map.json"),
        "rubric": read_json(root / "data/rubric.json"),
        "canon_events": read_json(root / "data/canon_events.json"),
        "act1_nodes": read_json(root / "data/act1_nodes.json"),
    }


def detect_structural_issues(state: dict[str, Any]) -> list[str]:
    story = state["story_map"]
    act_nodes = state["act1_nodes"]["nodes"]
    issues: list[str] = []

    # Unresolved graph pointers in the playable act graph.
    for node_id, node in act_nodes.items():
        direct_next = node.get("next")
        if direct_next and direct_next != "ACT2" and direct_next not in act_nodes:
            issues.append(f"{node_id} has unresolved next pointer {direct_next}")
        for archetype, target in (node.get("next_archetype") or {}).items():
            if target != "ACT2" and target not in act_nodes:
                issues.append(f"{node_id} next_archetype[{archetype}] points to missing {target}")
        for choice in node.get("choices", []):
            nxt = choice.get("next")
            if nxt and nxt != "ACT2" and nxt not in act_nodes:
                issues.append(f"{node_id} choice '{choice.get('label')}' points to missing {nxt}")

    # Every generated node must be reachable from the start and interactive.
    reachable = reachable_nodes(act_nodes, "1.0")
    for gen_id in sorted(n for n in act_nodes if n.startswith("gen_")):
        if gen_id not in reachable:
            issues.append(f"{gen_id} is not reachable from 1.0")
        if not act_nodes[gen_id].get("choices"):
            issues.append(f"{gen_id} has no choices")

    # Story map should mirror structural exits.
    for node_id, meta in story.get("nodes", {}).items():
        for nxt in meta.get("branches_to", []):
            if nxt != "ACT2" and nxt not in story.get("nodes", {}):
                issues.append(f"story_map {node_id} branches to missing {nxt}")

    # Branches open too long with no choke.
    open_branch_heads = []
    for node_id, meta in story.get("nodes", {}).items():
        if meta.get("type") == "branch":
            branches = meta.get("branches_to", [])
            if branches and all(
                story.get("nodes", {}).get(b, {}).get("type") != "choke"
                for b in branches
            ):
                open_branch_heads.append(node_id)
    if len(open_branch_heads) > 3:
        issues.append(f"branches open too long with no choke: {open_branch_heads}")

    # Acts with no tension increase.
    act_nodes_map = story.get("nodes", {})
    act_tension_deltas = [
        meta.get("tension_delta", 0)
        for meta in act_nodes_map.values()
    ]
    if act_tension_deltas and max(act_tension_deltas) <= 0:
        issues.append("no positive tension_delta found in any node")

    return issues


def reachable_nodes(nodes: dict[str, Any], start: str) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        node_id = stack.pop()
        if node_id == "ACT2" or node_id in seen or node_id not in nodes:
            continue
        seen.add(node_id)
        node = nodes[node_id]
        if node.get("next"):
            stack.append(node["next"])
        for target in (node.get("next_archetype") or {}).values():
            stack.append(target)
        for choice in node.get("choices", []):
            if choice.get("next"):
                stack.append(choice["next"])
    return seen


def acquire_lock():
    """Prevent overlapping evolution runs (the Telegram poll can block for hours)."""
    LOCK_PATH.parent.mkdir(exist_ok=True)
    handle = LOCK_PATH.open("w")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        return None
    return handle


def _load_script(name: str):
    """Load a module from scripts/ without package plumbing."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, str(REPO_ROOT / "scripts" / f"{name}.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def external_patterns(rubric: dict[str, Any]) -> list[str]:
    """Structural patterns from the weekly itch.io hunt — fed into the dramaturg."""
    analyses = rubric.get("external_analysis", [])
    if not analyses:
        return []
    patterns: list[str] = []
    for finding in analyses[-1].get("findings", []):
        for p in finding.get("analysis", {}).get("patterns", []):
            if p and p not in patterns:
                patterns.append(p)
    return patterns[:3]


def reader_feedback() -> list[str]:
    """Weakest-beat notes from the phantom reader-judge — fed into the dramaturg."""
    try:
        scores = read_json(DATA_DIR / "walk_scores.json")
    except Exception:
        return []
    notes = []
    for note in scores.get("reader_notes", [])[:4]:
        notes.append(
            f"{note.get('archetype')}: weakest beat was {note.get('weakest')} — "
            f"{note.get('reason', '')[:140]}"
        )
    return notes


def select_canon_event(state: dict[str, Any], preferred_id: str | None = None) -> dict[str, Any]:
    events = [event for event in state["canon_events"] if not event.get("used")]
    if not events:
        raise RuntimeError("No unused canon events remain")
    if preferred_id:
        for event in events:
            if event["id"] == preferred_id:
                return event
        raise RuntimeError(f"Preferred canon event {preferred_id} is unavailable or already used")

    story = state["story_map"]
    current_act = story.get("act", 2)
    current_role = story.get("dialectic_position", "establishing_antithesis")

    def event_score(event: dict[str, Any]) -> tuple[int, float]:
        role_match = int(event.get("dialectic_role") == current_role)
        act_match = int(event.get("act") == current_act)
        return (act_match + role_match, float(event.get("tension_level", 0)))

    return sorted(events, key=event_score, reverse=True)[0]


def next_generated_id(nodes: dict[str, Any]) -> str:
    index = 1
    while f"gen_{index}" in nodes:
        index += 1
    return f"gen_{index}"


def generate_node(state: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    """Generate one canon-rooted node by calling the local Qwen model."""
    seed = event["voyd_pov"].strip().lower().replace("—", " ")
    event_id = event["id"]
    story = state["story_map"]
    current_act = story.get("act", 2)
    current_role = story.get("dialectic_position", "establishing_antithesis")

    # Show the generator what readers stumbled on, not just the dramaturg —
    # otherwise it can repeat the exact flagged mistake and waste the night's cycle.
    complaints = reader_feedback()
    complaints_block = ""
    if complaints:
        complaints_block = (
            "\nPhantom readers flagged these weaknesses in recent beats. "
            "Do not repeat them:\n"
            + "\n".join(f"- {c}" for c in complaints) + "\n"
        )

    prompt = textwrap.dedent(f"""\
        You are the Voyd. Extend the following seed into a full dramatic beat.

        Current story position: act {current_act}, {current_role}
        Canon event: {event_id}
        Seed: {seed}
        {complaints_block}
        Requirements:
        - First person, from the Voyd's perspective
        - Entirely lowercase
        - 3-5 short declarative sentences
        - Specific, not abstract. Name concrete things.
        - No evasion. Do not obscure. Reveal directly.
        - Patient, seductive, slightly wrong in the way fate is slightly wrong.
        - Do not begin with "i".
        - Never use: certainly, of course, indeed, i understand, i feel, i sense, ancient, vast, eternal, whisper, shadows, abyss.
        - Never use em dashes.
        - Incorporate the seed's core image. Do not lose it.

        Also generate 2 choice labels for the player:
        - One "feed" choice (advances, increases portal value)
        - One "starve" choice (withdraws, decreases portal value)

        Return ONLY JSON in this exact format:
        {{
          "text": "...",
          "choices": [
            {{"label": "...", "type": "feed", "delta": 3}},
            {{"label": "...", "type": "starve", "delta": -2}}
          ]
        }}
    """)

    try:
        raw = qwen_chat([{"role": "user", "content": prompt}], max_tokens=300, temperature=0.9)
        raw = raw.strip()
        # Extract JSON block if wrapped in markdown
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        parsed = json.loads(raw)
        text = parsed["text"].strip().lower().replace("—", " ")
        choices = parsed["choices"]
    except Exception as exc:
        log(f"LLM generation failed ({exc}); falling back to seed extension")
        text = seed
        if not text.endswith("."):
            text += "."
        text += " i kept the part that wanted to move. i gave back the part that could be used."
        choices = [
            {"label": "feed the wanting", "type": "feed", "delta": 3, "next": "ACT2"},
            {"label": "starve the place it was", "type": "starve", "delta": -2, "next": "ACT2"},
        ]

    # Ensure next pointers exist
    for choice in choices:
        choice.setdefault("next", "ACT2")

    return {
        "label": event_id,
        "text": text,
        "delta": 3,
        "choices": choices,
        "source": "canon_evolution",
        "canon_event": event_id,
        "dialectic_role": event.get("dialectic_role", "establishing_antithesis"),
        "type": "beat",
        "act": event.get("act", story.get("act", 2)),
        "tension_delta": round(float(event.get("tension_level", 0.5)) - float(story.get("tension_level", 0.0)), 2),
        "seed": seed,
    }


def get_last_nodes(act1_nodes: dict[str, Any], count: int = 3) -> list[dict[str, Any]]:
    """Get the last N promoted/generated nodes as context."""
    promoted = [
        (nid, n) for nid, n in act1_nodes.get("nodes", {}).items()
        if n.get("promoted_at") or n.get("source") == "generated"
    ]
    promoted.sort(key=lambda x: x[1].get("promoted_at", "1970-01-01"))
    return [n for _, n in promoted[-count:]]


def score_node(node: dict[str, Any], rubric: dict[str, Any], act1_nodes: dict[str, Any],
               context_nodes: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Dramaturgical evaluation via Qwen on the rubric's three axes (0-10 each, total 0-30).

    context_nodes overrides the default last-promoted context — needed when judging a
    rewrite, whose position in the graph is not at the frontier.
    """
    if context_nodes is None:
        context_nodes = get_last_nodes(act1_nodes)
    context_texts = []
    for i, ctx in enumerate(context_nodes, 1):
        ctx_text = ctx.get("text", "")[:200]
        context_texts.append(f"Scene {i}: {ctx_text}")
    context_block = "\n\n".join(context_texts) if context_texts else "No previous scenes."

    current_text = node.get("text", "")
    choices = node.get("choices", [])
    choice_text = "\n".join(f"- {c.get('label', '')}" for c in choices)

    axis_lines = []
    for axis in SCORE_AXES:
        desc = rubric.get("axes", {}).get(axis, {}).get("description", "")
        axis_lines.append(f"- {axis}: {desc}")

    feedback_block = ""
    notes = reader_feedback()
    if notes:
        feedback_block += (
            "\nWHAT THE LAST READER FOUND WEAK (the new scene must not repeat these failures):\n"
            + "\n".join(f"- {n}" for n in notes) + "\n"
        )
    patterns = external_patterns(rubric)
    if patterns:
        feedback_block += (
            "\nSTRUCTURAL PATTERNS FROM TOP-RATED INTERACTIVE FICTION:\n"
            + "\n".join(f"- {p}" for p in patterns) + "\n"
        )

    prompt = (
        "You are a dramaturg who has internalized the entire dramatic canon: Greek tragedy, "
        "Shakespeare, Chekhov, Ibsen, Dostoevsky, the strongest film and interactive fiction "
        "ever made. Judge this scene against the strongest beats in that canon, not against "
        "amateur work. Your anchors for a 10: the recognition in Oedipus, the bargain in "
        "Faust, the door closing at the end of A Doll's House, the gun on the wall finally "
        "firing in Chekhov, the moment in Gatsby where wanting is revealed as the wound. "
        "A scene that merely sounds dark scores low. A scene that makes the next question "
        "harder to live with scores high.\n\n"
        f"PREVIOUS SCENES:\n{context_block}\n\n"
        f"NEW SCENE:\n{current_text}\n\n"
        f"CHOICES PRESENTED:\n{choice_text}\n"
        f"{feedback_block}\n"
        "Score the scene 0-10 on each of these axes:\n"
        + "\n".join(axis_lines) + "\n\n"
        "Respond in exactly this format:\n"
        "DIALECTIC_FUNCTION: <0-10>\n"
        "TENSION_ADVANCEMENT: <0-10>\n"
        "BRANCH_CHOKE_LOGIC: <0-10>\n"
        "PRECEDENT: <the closest dramatic precedent in the canon, and whether this scene earns the comparison>\n"
        "REASON: <one short paragraph>"
    )

    promote_threshold = rubric.get("auto_promote_threshold", AUTO_PROMOTE_DEFAULT)
    kill_threshold = rubric.get("auto_kill_threshold", AUTO_KILL_DEFAULT)

    try:
        raw = qwen_chat([{"role": "user", "content": prompt}], max_tokens=300, temperature=0.7)
    except Exception as exc:
        log(f"Dramaturg scoring failed ({exc}); defaulting to uncertain")
        axes = {axis: 6 for axis in SCORE_AXES}
        return {
            "axes": axes,
            "total": sum(axes.values()),
            "reason": f"scoring error: {exc}",
            "decision": "uncertain",
            "raw": "",
        }

    axes = {}
    for axis in SCORE_AXES:
        match = re.search(rf"{axis}\s*:\s*(\d+)", raw, re.IGNORECASE)
        value = int(match.group(1)) if match else 6
        axes[axis] = max(0, min(10, value))

    reason = raw.strip()
    reason_match = re.search(r"REASON\s*:\s*(.+)", raw, re.IGNORECASE | re.DOTALL)
    if reason_match:
        reason = reason_match.group(1).strip()

    precedent = None
    precedent_match = re.search(r"PRECEDENT\s*:\s*(.+)", raw, re.IGNORECASE)
    if precedent_match:
        precedent = precedent_match.group(1).strip()

    total = sum(axes.values())
    decision = (
        "promote" if total >= promote_threshold
        else "kill" if total < kill_threshold
        else "uncertain"
    )

    return {
        "axes": axes,
        "total": total,
        "reason": reason,
        "precedent": precedent,
        "decision": decision,
        "raw": raw,
    }


def find_act2_frontier(nodes: dict[str, Any]) -> list[str]:
    """All nodes with a choice pointing at ACT2 — the same topology phantom walkers test."""
    frontier: list[str] = []
    for node_id, node in nodes.items():
        if any(choice.get("next") == "ACT2" for choice in node.get("choices", [])):
            frontier.append(node_id)
    return sorted(frontier)


def promote_node(state: dict[str, Any], node: dict[str, Any], score: dict[str, Any], root: Path = REPO_ROOT) -> str:
    act_data = state["act1_nodes"]
    story = state["story_map"]
    events = state["canon_events"]
    rubric = state["rubric"]
    nodes = act_data["nodes"]
    new_id = next_generated_id(nodes)
    now = datetime.now().isoformat()
    frontier = find_act2_frontier(nodes)

    for frontier_id in frontier:
        for choice in nodes[frontier_id].get("choices", []):
            if choice.get("next") == "ACT2":
                choice["next"] = new_id

    # Keep the raw LLM transcript out of data shipped to players' browsers.
    stored_score = {k: v for k, v in score.items() if k != "raw"}

    promoted = dict(node)
    promoted.update({
        "id": new_id,
        "label": node.get("label", new_id),
        "score": stored_score,
        "promoted_at": now,
    })
    nodes[new_id] = promoted
    act_data.setdefault("meta", {})["last_evolved"] = now
    act_data["meta"]["promoted_nodes"] = act_data["meta"].get("promoted_nodes", 0) + 1

    # Mirror branch changes in story_map.
    for frontier_id in frontier:
        if frontier_id in story["nodes"]:
            story["nodes"][frontier_id]["branches_to"] = [
                new_id if nxt == "ACT2" else nxt for nxt in story["nodes"][frontier_id].get("branches_to", [])
            ]
    branches_to = []
    for choice in node.get("choices", []):
        if choice["next"] not in branches_to:
            branches_to.append(choice["next"])
    story["nodes"][new_id] = {
        "id": new_id,
        "type": node.get("type", "beat"),
        "act": node.get("act", story.get("act", 2)),
        "dialectic_role": node.get("dialectic_role"),
        "tension_delta": node.get("tension_delta", 0),
        "branches_to": branches_to,
        "converges_from": frontier,
        "canon_event": node.get("canon_event"),
        "score": stored_score,
    }
    current_tension = float(story.get("tension_level", 0))
    story["tension_level"] = round(current_tension + max(0, node.get("tension_delta", 0)), 2)
    story["open_branches"] = branches_to

    for event in events:
        if event.get("id") == node.get("canon_event"):
            event["used"] = True
            event["used_at"] = now
            event["node_id"] = new_id

    record_decision(rubric, {
        "at": now,
        "node_id": new_id,
        "canon_event": node.get("canon_event"),
        "score": score,
        "decision": "promote",
    })

    write_json(root / "data/act1_nodes.json", act_data)
    write_json(root / "data/story_map.json", story)
    write_json(root / "data/canon_events.json", events)
    write_json(root / "data/rubric.json", rubric)
    return new_id


def recalibrate_rubric(rubric: dict[str, Any]) -> None:
    """Analyze the last 10 axis-scored decisions and adjust weights based on patterns."""
    scored = [
        d for d in rubric.get("decisions", [])
        if isinstance(d.get("score"), dict) and isinstance(d["score"].get("axes"), dict)
    ]
    if len(scored) < 5:
        return

    recent = scored[-10:]
    axes_names = list(SCORE_AXES)
    means = {axis: sum(d["score"]["axes"].get(axis, 0) for d in recent) / len(recent) for axis in axes_names}
    thresholds = {axis: rubric["axes"][axis]["threshold"] for axis in axes_names}

    # Compute drift: how far each axis mean is from its threshold, normalized
    drifts = {}
    for axis in axes_names:
        drifts[axis] = (means[axis] - thresholds[axis]) / 10.0

    # If an axis consistently scores far above threshold, reduce weight slightly.
    # If consistently near or below threshold, increase weight.
    base_weights = {axis: rubric["axes"][axis]["weight"] for axis in axes_names}
    adjustments = {}
    for axis in axes_names:
        drift = drifts[axis]
        if drift > 0.3:
            adjustments[axis] = -0.03
        elif drift < 0.0:
            adjustments[axis] = +0.03
        else:
            adjustments[axis] = 0.0

    new_weights = {axis: max(0.1, base_weights[axis] + adjustments[axis]) for axis in axes_names}
    total = sum(new_weights.values())
    new_weights = {axis: round(w / total, 2) for axis, w in new_weights.items()}

    now = datetime.now().isoformat()
    rubric["last_recalibrated"] = now
    rubric["pending_weight_suggestion"] = {
        **new_weights,
        "reason": (
            f"recalibrated from last {len(recent)} decisions. "
            f"means: {means}. drifts from threshold: {drifts}."
        ),
    }
    # Apply the new weights immediately
    for axis in axes_names:
        rubric["axes"][axis]["weight"] = new_weights[axis]


def record_decision(rubric: dict[str, Any], entry: dict[str, Any]) -> None:
    """Append a decision and recalibrate weights after every 5 decisions (directive step 10)."""
    decisions = rubric.setdefault("decisions", [])
    decisions.append(entry)
    if len(decisions) % 5 == 0:
        recalibrate_rubric(rubric)


def send_structural_issues_to_telegram(issues: list[str]) -> bool:
    env = {**load_dotenv(), **os.environ}
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHAT_ID") or env.get("TELEGRAM_HOME_CHANNEL")
    if not token or not chat_id:
        log("Telegram credentials missing; cannot send structural issues")
        return False
    message = textwrap.dedent(f"""
    🚨 Voyd structural issues detected.

    {chr(10).join(f'- {issue}' for issue in issues)}

    Evolution halted until resolved.
    """)
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": message.strip()}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            ok = response.status == 200
            log(f"Sent structural issues to Telegram: {ok}")
            return ok
    except Exception as exc:
        log(f"Telegram send failed: {exc}")
        return False


def send_uncertain_node_to_telegram(node: dict[str, Any], score: dict[str, Any]) -> bool:
    env = {**load_dotenv(), **os.environ}
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHAT_ID") or env.get("TELEGRAM_HOME_CHANNEL")
    if not token or not chat_id:
        log("Telegram credentials missing; cannot send uncertain node")
        return False
    message = textwrap.dedent(f"""
    Voyd evolution needs approval.

    Canon event: {node.get('canon_event')}
    Score: {score.get('total')} / 30
    Axes: {score.get('axes')}

    Node:
    {node.get('text')}

    Reply YES / NO / NOT YET.
    """).strip()
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": message}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            ok = response.status == 200
            log(f"Sent uncertain node to Telegram: {ok}")
            return ok
    except Exception as exc:
        log(f"Telegram send failed: {exc}")
        return False


def send_telegram_text(text: str) -> bool:
    env = {**load_dotenv(), **os.environ}
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHAT_ID") or env.get("TELEGRAM_HOME_CHANNEL")
    if not token or not chat_id:
        log("Telegram credentials missing; cannot send message")
        return False
    data = urllib.parse.urlencode({"chat_id": chat_id, "text": text.strip()}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            return response.status == 200
    except Exception as exc:
        log(f"Telegram send failed: {exc}")
        return False


# ---------------------------------------------------------------------------
# IMMUNE SYSTEM — heal_structural_issues (see AGENTS.md, Planned Infrastructure)
# Active only once data/walk_history.jsonl holds >= IMMUNE_WALK_GATE records.
# Auto-applies a fix only when the generated node scores >= HEAL_AUTO_THRESHOLD;
# otherwise the proposed fix goes to Patrick on Telegram.
# ---------------------------------------------------------------------------

def log_heal(entry: dict[str, Any]) -> None:
    HEAL_LOG_PATH.parent.mkdir(exist_ok=True)
    entries = []
    if HEAL_LOG_PATH.exists():
        try:
            entries = json.loads(HEAL_LOG_PATH.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries.append(entry)
    HEAL_LOG_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def immune_active() -> tuple[bool, int]:
    try:
        pw = _load_script("phantom_walkers")
        count = pw.walk_history_count()
    except Exception:
        count = 0
    return count >= IMMUNE_WALK_GATE, count


def detect_stranded_chokes(story: dict[str, Any]) -> list[tuple[str, str]]:
    """Generated choke nodes that some branch head cannot reach.

    Authored chokes (the parallel archetype act-breaks) are exempt: they are
    parallel by design. Only gen_* chokes are expected to catch all branches.
    """
    nodes = story.get("nodes", {})
    chokes = [nid for nid, m in nodes.items()
              if m.get("type") == "choke" and nid.startswith("gen_")]
    heads = [nid for nid, m in nodes.items() if m.get("type") == "branch"]
    stranded = []
    for choke in chokes:
        for head in heads:
            seen: set = set()
            stack = [head]
            found = False
            while stack:
                cur = stack.pop()
                if cur == choke:
                    found = True
                    break
                if cur in seen or cur not in nodes:
                    continue
                seen.add(cur)
                stack.extend(nodes[cur].get("branches_to", []))
            if not found:
                stranded.append((head, choke))
    return stranded


def _select_heal_event(state: dict[str, Any], roles: set, highest: bool) -> dict[str, Any] | None:
    events = [e for e in state["canon_events"]
              if not e.get("used") and (not roles or e.get("dialectic_role") in roles)]
    if not events:
        return None
    return sorted(events, key=lambda e: float(e.get("tension_level", 0)), reverse=highest)[0]


def _apply_heal(state: dict[str, Any], node: dict[str, Any], event: dict[str, Any],
                issue_type: str) -> bool:
    score = score_node(node, state["rubric"], state["act1_nodes"])
    entry = {
        "at": datetime.now().isoformat(),
        "issue_type": issue_type,
        "canon_event_used": event["id"],
        "score": {k: v for k, v in score.items() if k != "raw"},
    }
    if score["total"] >= HEAL_AUTO_THRESHOLD:
        node_id = promote_node(state, node, score, REPO_ROOT)
        run_build(REPO_ROOT)
        entry.update({"applied": True, "nodes_changed": [node_id],
                      "reason": f"auto-heal: score {score['total']} >= {HEAL_AUTO_THRESHOLD}"})
        log_heal(entry)
        log(f"Healed {issue_type} with {node_id} (score {score['total']}/30)")
        return True
    entry.update({"applied": False, "nodes_changed": [],
                  "reason": f"score {score['total']} below heal threshold {HEAL_AUTO_THRESHOLD}"})
    log_heal(entry)
    send_telegram_text(
        f"🩹 Voyd immune system: proposed fix for '{issue_type}' scored "
        f"{score['total']}/30 (needs {HEAL_AUTO_THRESHOLD}). Not applied.\n\n"
        f"Canon event: {event['id']}\n\nNode:\n{node.get('text')}\n\n"
        f"Apply manually or wait for a stronger candidate."
    )
    return False


def heal_open_branches(state: dict[str, Any]) -> bool:
    """Case 1: branches open too long with no choke — generate a convergence node."""
    event = _select_heal_event(state, {"turn", "act_break"}, highest=False)
    if not event:
        log("heal: no unused turn/act_break canon event for convergence")
        return False
    node = generate_node(state, event)
    node["type"] = "choke"
    story_nodes = state["story_map"].get("nodes", {})
    heads = [m for m in story_nodes.values() if m.get("type") == "branch"]
    deltas = [h.get("tension_delta", 0) for h in heads] or [0]
    node["tension_delta"] = round(sum(deltas) / len(deltas) + 0.1, 2)
    return _apply_heal(state, node, event, "open_branches_no_choke")


def heal_flat_act(state: dict[str, Any]) -> bool:
    """Case 2: no tension increase — generate an escalation node at the frontier."""
    story = state["story_map"]
    events = [e for e in state["canon_events"] if not e.get("used")]
    matching = [e for e in events
                if e.get("act") == story.get("act")
                and e.get("dialectic_role") == story.get("dialectic_position")] or events
    if not matching:
        log("heal: no unused canon events for escalation")
        return False
    event = sorted(matching, key=lambda e: float(e.get("tension_level", 0)), reverse=True)[0]
    node = generate_node(state, event)
    node["tension_delta"] = max(0.15, float(node.get("tension_delta", 0)))
    return _apply_heal(state, node, event, "flat_act_no_tension")


def heal_stranded_choke(state: dict[str, Any], head: str, choke: str) -> bool:
    """Case 3: a branch head cannot reach a generated choke — build a bridge beat."""
    act_nodes = state["act1_nodes"]["nodes"]
    head_node = act_nodes.get(head)
    if not head_node:
        return False
    dangling = [c for c in head_node.get("choices", [])
                if c.get("next") == "ACT2" or c.get("next") not in act_nodes]
    if not dangling:
        log(f"heal: branch head {head} has no dangling exit to bridge from; manual fix needed")
        return False
    events = [e for e in state["canon_events"] if not e.get("used")]
    if not events:
        log("heal: no unused canon events for bridge")
        return False
    event = sorted(events, key=lambda e: float(e.get("tension_level", 0)))[0]
    node = generate_node(state, event)
    node["type"] = "beat"
    for choice in node["choices"]:
        choice["next"] = choke

    score = score_node(node, state["rubric"], state["act1_nodes"])
    entry = {
        "at": datetime.now().isoformat(),
        "issue_type": "stranded_choke",
        "canon_event_used": event["id"],
        "score": {k: v for k, v in score.items() if k != "raw"},
    }
    if score["total"] < HEAL_AUTO_THRESHOLD:
        entry.update({"applied": False, "nodes_changed": [],
                      "reason": f"bridge score {score['total']} below {HEAL_AUTO_THRESHOLD}"})
        log_heal(entry)
        send_telegram_text(
            f"🩹 Voyd immune system: bridge from {head} to {choke} scored "
            f"{score['total']}/30. Not applied.\n\nNode:\n{node.get('text')}"
        )
        return False

    new_id = next_generated_id(act_nodes)
    now = datetime.now().isoformat()
    node.update({"id": new_id, "score": {k: v for k, v in score.items() if k != "raw"},
                 "promoted_at": now})
    for choice in dangling:
        choice["next"] = new_id
    act_nodes[new_id] = node
    state["act1_nodes"].setdefault("meta", {})["last_evolved"] = now

    story = state["story_map"]
    story["nodes"][new_id] = {
        "id": new_id, "type": "beat", "act": node.get("act", story.get("act", 2)),
        "dialectic_role": node.get("dialectic_role"),
        "tension_delta": node.get("tension_delta", 0),
        "branches_to": [choke], "converges_from": [head],
        "canon_event": event["id"],
    }
    if head in story["nodes"]:
        branches = story["nodes"][head].setdefault("branches_to", [])
        if new_id not in branches:
            branches.append(new_id)
    for ev in state["canon_events"]:
        if ev.get("id") == event["id"]:
            ev["used"] = True
            ev["used_at"] = now
            ev["node_id"] = new_id
    record_decision(state["rubric"], {
        "at": now, "node_id": new_id, "canon_event": event["id"],
        "score": score, "decision": "promote",
        "reason": f"immune bridge {head} -> {choke}",
    })
    write_json(REPO_ROOT / "data/act1_nodes.json", state["act1_nodes"])
    write_json(REPO_ROOT / "data/story_map.json", story)
    write_json(CANON_EVENTS_PATH, state["canon_events"])
    write_json(RUBRIC_PATH, state["rubric"])
    run_build(REPO_ROOT)
    entry.update({"applied": True, "nodes_changed": [new_id, head],
                  "reason": f"bridge {head} -> {new_id} -> {choke}"})
    log_heal(entry)
    log(f"Healed stranded choke: {head} -> {new_id} -> {choke}")
    return True


def heal_structural_issues(state: dict[str, Any], issues: list[str],
                           stranded: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    """Attempt to close detected wounds autonomously. Returns (healed, remaining)."""
    active, count = immune_active()
    all_issues = issues + [f"choke {c} strands branch head {h}" for h, c in stranded]
    if not active:
        log(f"Immune system dormant ({count}/{IMMUNE_WALK_GATE} walk records); cannot auto-heal")
        return [], all_issues

    healed: list[str] = []
    remaining: list[str] = []
    for issue in issues:
        if "branches open too long with no choke" in issue:
            ok = heal_open_branches(state)
        elif "no positive tension_delta" in issue:
            ok = heal_flat_act(state)
        else:
            ok = False  # pointer corruption etc. needs a human or a code fix
        (healed if ok else remaining).append(issue)
    for head, choke in stranded:
        ok = heal_stranded_choke(state, head, choke)
        (healed if ok else remaining).append(f"choke {choke} strands branch head {head}")
    return healed, remaining


def post_cycle(state: dict[str, Any], cycle_summary: str | None = None) -> None:
    """Self-play after every resolved cycle: walk all archetypes, judge, record, report."""
    try:
        pw = _load_script("phantom_walkers")
        report, _ = pw.run_walks()
        pw.record_run(report)
        history = pw.walk_history_count()
        log(
            f"Self-play complete: kills_recommended={report['kills_recommended']} "
            f"flags={len(report['flags'])} reader_notes={len(report.get('reader_notes', []))} "
            f"history={history} records"
        )
        pw.send_telegram(pw.build_report_message(
            report,
            nodes=state["act1_nodes"]["nodes"],
            cycle_summary=cycle_summary,
        ))
    except Exception as exc:
        log(f"Self-play failed: {exc}")


def get_latest_update_id(token: str) -> int:
    """Fetch the latest update_id from Telegram to establish a baseline."""
    url = f"https://api.telegram.org/bot{token}/getUpdates?limit=1"
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            data = json.loads(response.read())
            results = data.get("result", [])
            if results:
                return results[-1]["update_id"]
    except Exception:
        pass
    return 0


def poll_telegram_for_reply(token: str, chat_id: str, timeout_seconds: int = 86400, poll_interval: int = 30) -> str | None:
    """Poll Telegram for Patrick's YES/NO/NOT YET reply. Returns the reply or None on timeout."""
    last_update_id = get_latest_update_id(token)
    deadline = time.time() + timeout_seconds
    log(f"Polling Telegram for reply (timeout {timeout_seconds}s)")

    while time.time() < deadline:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={last_update_id + 1}&limit=10"
            with urllib.request.urlopen(url, timeout=20) as response:
                data = json.loads(response.read())
                for update in data.get("result", []):
                    last_update_id = max(last_update_id, update["update_id"])
                    message = update.get("message", {})
                    if str(message.get("chat", {}).get("id")) != str(chat_id):
                        continue
                    text = message.get("text", "").strip().upper()
                    if text in ("YES", "NO", "NOT YET"):
                        log(f"Received Telegram reply: {text}")
                        return text
        except Exception as exc:
            log(f"Polling error: {exc}")
        time.sleep(poll_interval)

    log("Telegram poll timed out")
    return None


def run_build(root: Path = REPO_ROOT) -> None:
    subprocess.run([sys.executable, str(root / "build_frontend.py")], cwd=root, check=True)


DATA_COMMIT_PATHS = ("data", "frontend/voyd_data.json")


def commit_data_changes(root: Path = REPO_ROOT) -> bool:
    """Commit and push this cycle's data changes on the checked-out feat branch.

    The public site deploys only from main, so the organism's nightly growth is
    invisible until a human merge; committing to the working branch keeps every
    cycle one merge away from live. Never touches main or a detached HEAD — in
    that case the changes simply stay in the working tree. A failed push keeps
    the commit local and is only logged.
    """
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)

    branch = git("rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    if branch in ("", "HEAD", "main"):
        log(f"Data changes left uncommitted (checked out: {branch or 'unknown'})")
        return False
    status = git("status", "--porcelain", "--", *DATA_COMMIT_PATHS).stdout
    if not status.strip():
        return False
    changed = sorted({Path(line[3:].strip().strip('"')).name for line in status.strip().splitlines()})
    git("add", "-A", "--", *DATA_COMMIT_PATHS)
    message = f"chore(organism): cycle data — {', '.join(changed)}"
    commit = git("commit", "-m", message, "--", *DATA_COMMIT_PATHS)
    if commit.returncode != 0:
        log(f"Data commit failed: {(commit.stderr or commit.stdout).strip()[:200]}")
        return False
    push = git("push", "origin", f"HEAD:{branch}")
    if push.returncode != 0:
        log(f"Data push failed; commit kept local: {(push.stderr or push.stdout).strip()[:200]}")
    else:
        log(f"Committed and pushed data changes to {branch}: {message}")
    return True


def run_phantom_gate(node: dict[str, Any], state: dict[str, Any]) -> float:
    """Insert the candidate into a copy of the graph, walk it, return min path uniqueness."""
    pw = _load_script("phantom_walkers")
    log("Running phantom walker uniqueness test...")
    min_uniqueness, _ = pw.test_candidate(node, state["act1_nodes"])
    log(f"Phantom walker min uniqueness: {min_uniqueness}")
    return min_uniqueness


def gated_promote(state: dict[str, Any], node: dict[str, Any], score: dict[str, Any],
                  event: dict[str, Any], context: str) -> int:
    """Reverse pipeline: phantom walkers must pass before promotion."""
    node["id"] = next_generated_id(state["act1_nodes"]["nodes"])
    min_uniqueness = run_phantom_gate(node, state)
    if min_uniqueness < PHANTOM_UNIQUENESS_FLOOR:
        record_decision(state["rubric"], {
            "at": datetime.now().isoformat(),
            "canon_event": event["id"],
            "score": score,
            "decision": "kill",
            "reason": (
                f"{context} but phantom walker uniqueness {min_uniqueness} "
                f"below {PHANTOM_UNIQUENESS_FLOOR}"
            ),
        })
        write_json(RUBRIC_PATH, state["rubric"])
        log(f"Killed generated node for {event['id']} — uniqueness too low ({min_uniqueness})")
        post_cycle(state, cycle_summary=(
            f"🪓 Tonight's draft (from '{event['id']}') passed the dramaturg but was killed: "
            f"with it spliced in, walk uniqueness fell to {min_uniqueness} "
            f"(floor {PHANTOM_UNIQUENESS_FLOOR}). The event stays in the larder."
        ))
        return 0
    node_id = promote_node(state, node, score, REPO_ROOT)
    run_build(REPO_ROOT)
    log(f"Promoted {node_id} from canon event {event['id']} ({context})")
    post_cycle(state, cycle_summary=(
        f"🌱 The story grew a new beat tonight: {node_id} "
        f"(from canon event '{event['id']}', {context}).\n"
        f"“{node['text'][:220]}”"
    ))
    return 0


def main(argv: list[str] | None = None) -> int:
    lock = acquire_lock()
    if lock is None:
        log("Another evolve.py run holds the lock; exiting")
        return 4
    try:
        return run_cycle(argv)
    finally:
        commit_data_changes()


def run_cycle(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    preferred = argv[0] if argv else os.environ.get("VOYD_CANON_EVENT")
    state = load_state(REPO_ROOT)

    # Detect wounds; try to heal them before halting (immune system).
    issues = detect_structural_issues(state)
    stranded = detect_stranded_chokes(state["story_map"])
    if issues or stranded:
        for issue in issues:
            log(f"STRUCTURAL ISSUE: {issue}")
        healed, remaining = heal_structural_issues(state, issues, stranded)
        if remaining:
            send_structural_issues_to_telegram(remaining)
            return 2
        log(f"All structural issues healed autonomously: {healed}")
        state = load_state(REPO_ROOT)

    # Keep the larder stocked: mine new canon events from the books when low.
    unused = [e for e in state["canon_events"] if not e.get("used")]
    if len(unused) < MINE_WHEN_UNUSED_BELOW:
        log(f"Canon larder low ({len(unused)} unused); mining the books")
        try:
            miner = _load_script("mine_canon")
            mined = miner.mine(max_accept=5)
            if mined:
                send_telegram_text(
                    "⛏️ Mined new canon events:\n"
                    + "\n".join(f"- {e['id']} (tension {e['tension_level']}, {e['dialectic_role']})"
                                for e in mined)
                )
                state = load_state(REPO_ROOT)
        except Exception as exc:
            log(f"Mining failed: {exc}")

    try:
        event = select_canon_event(state, preferred_id=preferred)
    except RuntimeError as exc:
        log(f"No evolution possible: {exc}")
        return 0
    log(f"Selected canon event: {event['id']}")
    node = generate_node(state, event)
    score = score_node(node, state["rubric"], state["act1_nodes"])
    log(
        f"Generated node score: {score['total']}/30 axes={score['axes']} "
        f"reason={score['reason'][:60]} decision={score['decision']}"
    )

    if score["decision"] == "promote":
        return gated_promote(state, node, score, event, f"dramaturg total {score['total']}")

    if score["decision"] == "kill":
        record_decision(state["rubric"], {
            "at": datetime.now().isoformat(),
            "canon_event": event["id"],
            "score": score,
            "decision": "kill",
            "reason": "score below auto_kill_threshold",
        })
        write_json(RUBRIC_PATH, state["rubric"])
        log(f"Killed generated node for {event['id']}")
        post_cycle(state, cycle_summary=(
            f"🪓 Tonight's draft (from '{event['id']}') was killed by the dramaturg "
            f"at {score['total']}/30: {score['reason'][:220]}"
        ))
        return 0

    # Uncertain zone: send to Telegram and wait for reply
    sent = send_uncertain_node_to_telegram(node, score)
    if not sent:
        log("Failed to send uncertain node to Telegram; aborting")
        return 3

    env = {**load_dotenv(), **os.environ}
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHAT_ID") or env.get("TELEGRAM_HOME_CHANNEL")
    if not token or not chat_id:
        log("Telegram credentials missing; cannot poll for reply")
        return 3

    reply = poll_telegram_for_reply(token, chat_id)
    now = datetime.now().isoformat()

    if reply == "YES":
        return gated_promote(state, node, score, event, "Telegram YES")

    if reply == "NO":
        # Mark event as used per directive
        for ev in state["canon_events"]:
            if ev.get("id") == event["id"]:
                ev["used"] = True
                ev["used_at"] = now
                ev["decision"] = "killed_by_patrick"
        record_decision(state["rubric"], {
            "at": now,
            "canon_event": event["id"],
            "score": score,
            "decision": "kill",
            "reason": "Patrick replied NO on Telegram",
        })
        write_json(CANON_EVENTS_PATH, state["canon_events"])
        write_json(RUBRIC_PATH, state["rubric"])
        log(f"Killed generated node for {event['id']} (Telegram NO)")
        post_cycle(state, cycle_summary=(
            f"🪓 Killed tonight's draft from '{event['id']}' per your NO; "
            f"the event is marked used and retired."
        ))
        return 0

    if reply == "NOT YET":
        # Hold event as unused, note buildup needed
        record_decision(state["rubric"], {
            "at": now,
            "canon_event": event["id"],
            "score": score,
            "decision": "hold",
            "reason": "Patrick replied NOT YET on Telegram; more buildup needed",
        })
        write_json(RUBRIC_PATH, state["rubric"])
        log(f"Held event {event['id']} for future use (Telegram NOT YET)")
        return 0

    # Timeout or unrecognized reply
    log("No valid Telegram reply received; holding event")
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
