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

import json
import os
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
AUTO_PROMOTE_DEFAULT = 24
AUTO_KILL_DEFAULT = 18

QWEN_BASE_URL = "http://localhost:8081/v1"
QWEN_MODEL = "Qwen3.6-27B-Q6_K"

INTENSE_WORDS = {
    "grief", "loss", "want", "hunger", "dark", "silence", "fall", "depth",
    "void", "dream", "pain", "need", "fear", "longing", "weight", "sorrow",
    "break", "burn", "tear", "shatter", "crack", "pull", "open", "close",
    "bleed", "dissolve", "forget", "remember", "refuse", "resist", "hold",
    "release", "reach", "move", "step", "turn", "become", "drift", "drown",
    "hunger", "hunger", "wound", "scar", "ghost", "echo", "absence",
}

DYNAMIC_WORDS = {
    "reach", "pull", "open", "close", "fall", "break", "burn", "tear",
    "shatter", "move", "step", "turn", "become", "hold", "release",
    "feed", "starve", "grow", "double", "shift", "change", "rewrite",
}


def log(message: str) -> None:
    line = f"[{datetime.now().isoformat()}] {message}"
    print(line)
    LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    env_path = path or (Path.home() / ".hermes" / ".env")
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
        for choice in node.get("choices", []):
            nxt = choice.get("next")
            if nxt and nxt != "ACT2" and nxt not in act_nodes:
                issues.append(f"{node_id} choice '{choice.get('label')}' points to missing {nxt}")

    # Existing generated Act 2 nodes must be reachable from 10.0 and interactive.
    reachable = reachable_nodes(act_nodes, "10.0")
    for i in range(1, 20):
        gen_id = f"gen_{i}"
        if gen_id in act_nodes and gen_id not in reachable:
            issues.append(f"{gen_id} is not reachable from 10.0")
        if gen_id in act_nodes and not act_nodes[gen_id].get("choices"):
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
        for choice in node.get("choices", []):
            if choice.get("next"):
                stack.append(choice["next"])
    return seen


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

    prompt = textwrap.dedent(f"""\
        You are the Voyd. Extend the following seed into a full dramatic beat.

        Current story position: act {current_act}, {current_role}
        Canon event: {event_id}
        Seed: {seed}

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


def score_node(node: dict[str, Any], rubric: dict[str, Any], story_map: dict[str, Any]) -> dict[str, Any]:
    axes: dict[str, int] = {}
    text = node["text"]
    current_role = story_map.get("dialectic_position")

    dialectic = 5
    if node.get("dialectic_role") == current_role:
        dialectic += 3
    if node.get("canon_event"):
        dialectic += 1
    if node.get("act") == story_map.get("act"):
        dialectic += 1
    axes["dialectic_function"] = min(10, dialectic)

    tension = 5
    if node.get("tension_delta", 0) > 0:
        tension += 2
    # Event-agnostic intensity scoring
    text_words = set(text.lower().split())
    intense_hits = len(text_words & INTENSE_WORDS)
    dynamic_hits = len(text_words & DYNAMIC_WORDS)
    if intense_hits >= 2:
        tension += 1
    if dynamic_hits >= 2:
        tension += 1
    sentences = [s for s in text.split(".") if s.strip()]
    if 3 <= len(sentences) <= 5:
        tension += 1
    axes["tension_advancement"] = min(10, tension)

    branch = 5
    choices = node.get("choices", [])
    if len(choices) == 2:
        branch += 2
    if {choice.get("type") for choice in choices} == {"feed", "starve"}:
        branch += 2
    if all(choice.get("next") for choice in choices):
        branch += 1
    axes["branch_choke_logic"] = min(10, branch)

    total = sum(axes.values())
    return {
        "axes": axes,
        "total": total,
        "decision": (
            "promote" if total >= rubric.get("auto_promote_threshold", AUTO_PROMOTE_DEFAULT)
            else "kill" if total < rubric.get("auto_kill_threshold", AUTO_KILL_DEFAULT)
            else "uncertain"
        ),
    }


def find_act2_frontier(nodes: dict[str, Any]) -> list[str]:
    frontier: list[str] = []
    for node_id, node in nodes.items():
        if not node_id.startswith("gen_"):
            continue
        if any(choice.get("next") == "ACT2" for choice in node.get("choices", [])):
            frontier.append(node_id)
    return sorted(frontier, key=lambda item: int(item.split("_", 1)[1]))


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

    promoted = dict(node)
    promoted.update({
        "id": new_id,
        "label": node.get("label", new_id),
        "score": score,
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
    story["nodes"][new_id] = {
        "id": new_id,
        "type": node.get("type", "beat"),
        "act": node.get("act", story.get("act", 2)),
        "dialectic_role": node.get("dialectic_role"),
        "tension_delta": node.get("tension_delta", 0),
        "branches_to": [choice["next"] for choice in node.get("choices", [])],
        "converges_from": frontier,
        "canon_event": node.get("canon_event"),
        "score": score,
    }
    current_tension = float(story.get("tension_level", 0))
    story["tension_level"] = round(current_tension + max(0, node.get("tension_delta", 0)), 2)
    story["open_branches"] = ["ACT2"]
    story["structural_issues"] = []

    for event in events:
        if event.get("id") == node.get("canon_event"):
            event["used"] = True
            event["used_at"] = now
            event["node_id"] = new_id

    rubric.setdefault("decisions", []).append({
        "at": now,
        "node_id": new_id,
        "canon_event": node.get("canon_event"),
        "score": score,
        "decision": "promote",
    })

    if len(rubric["decisions"]) % 5 == 0:
        recalibrate_rubric(rubric)

    write_json(root / "data/act1_nodes.json", act_data)
    write_json(root / "data/story_map.json", story)
    write_json(root / "data/canon_events.json", events)
    write_json(root / "data/rubric.json", rubric)
    return new_id


def recalibrate_rubric(rubric: dict[str, Any]) -> None:
    """Analyze the last 10 decisions and suggest adjusted weights based on patterns."""
    decisions = rubric.get("decisions", [])
    if len(decisions) < 5:
        return

    recent = decisions[-10:]
    axes_names = ["dialectic_function", "tension_advancement", "branch_choke_logic"]
    means = {axis: sum(d["score"]["axes"][axis] for d in recent) / len(recent) for axis in axes_names}
    thresholds = {
        "dialectic_function": rubric["axes"]["dialectic_function"]["threshold"],
        "tension_advancement": rubric["axes"]["tension_advancement"]["threshold"],
        "branch_choke_logic": rubric["axes"]["branch_choke_logic"]["threshold"],
    }

    # Compute drift: how far each axis mean is from its threshold, normalized
    drifts = {}
    for axis in axes_names:
        drifts[axis] = (means[axis] - thresholds[axis]) / 10.0

    # If an axis consistently scores far above threshold, reduce weight slightly.
    # If consistently near or below threshold, increase weight.
    base_weights = {
        "dialectic_function": 0.4,
        "tension_advancement": 0.35,
        "branch_choke_logic": 0.25,
    }
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


def send_structural_issues_to_telegram(issues: list[str]) -> bool:
    env = {**load_dotenv(), **os.environ}
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHAT_ID")
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
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHAT_ID")
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


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    preferred = argv[0] if argv else os.environ.get("VOYD_CANON_EVENT")
    state = load_state(REPO_ROOT)
    issues = detect_structural_issues(state)
    if issues:
        for issue in issues:
            log(f"STRUCTURAL ISSUE: {issue}")
        send_structural_issues_to_telegram(issues)
        return 2

    event = select_canon_event(state, preferred_id=preferred)
    log(f"Selected canon event: {event['id']}")
    node = generate_node(state, event)
    score = score_node(node, state["rubric"], state["story_map"])
    log(f"Generated node score: {score['total']} axes={score['axes']} decision={score['decision']}")

    if score["decision"] == "promote":
        node_id = promote_node(state, node, score, REPO_ROOT)
        run_build(REPO_ROOT)
        log(f"Promoted {node_id} from canon event {event['id']}")
        return 0

    if score["decision"] == "kill":
        state["rubric"].setdefault("decisions", []).append({
            "at": datetime.now().isoformat(),
            "canon_event": event["id"],
            "score": score,
            "decision": "kill",
            "reason": "score below auto_kill_threshold",
        })
        write_json(RUBRIC_PATH, state["rubric"])
        log(f"Killed generated node for {event['id']}")
        return 0

    # Uncertain zone: send to Telegram and wait for reply
    sent = send_uncertain_node_to_telegram(node, score)
    if not sent:
        log("Failed to send uncertain node to Telegram; aborting")
        return 3

    env = {**load_dotenv(), **os.environ}
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHAT_ID")
    if not token or not chat_id:
        log("Telegram credentials missing; cannot poll for reply")
        return 3

    reply = poll_telegram_for_reply(token, chat_id)
    now = datetime.now().isoformat()

    if reply == "YES":
        node_id = promote_node(state, node, score, REPO_ROOT)
        run_build(REPO_ROOT)
        log(f"Promoted {node_id} from canon event {event['id']} (Telegram YES)")
        return 0

    if reply == "NO":
        # Mark event as used per directive
        for ev in state["canon_events"]:
            if ev.get("id") == event["id"]:
                ev["used"] = True
                ev["used_at"] = now
                ev["decision"] = "killed_by_patrick"
        state["rubric"].setdefault("decisions", []).append({
            "at": now,
            "canon_event": event["id"],
            "score": score,
            "decision": "kill",
            "reason": "Patrick replied NO on Telegram",
        })
        write_json(CANON_EVENTS_PATH, state["canon_events"])
        write_json(RUBRIC_PATH, state["rubric"])
        log(f"Killed generated node for {event['id']} (Telegram NO)")
        return 0

    if reply == "NOT YET":
        # Hold event as unused, note buildup needed
        state["rubric"].setdefault("decisions", []).append({
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
