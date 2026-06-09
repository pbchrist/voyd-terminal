#!/usr/bin/env python3
"""
evolve.py — Evolves the Voyd Terminal narrative graph.

Simulates Act 1 traversal, generates a plausible human player answer at node 10.0,
then generates 3 Act 2 Voyd response nodes via the Kimi (Moonshot) API.
Nodes scoring voice + polarity + momentum >= 21 are promoted into data/act1_nodes.json.
"""

import json
import os
import random
import sys
import datetime
import subprocess
import textwrap
import urllib.request
import urllib.error
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).parent
VOYD_SYSTEM_MD = REPO_ROOT / "data" / "voyd_system.md"
ACT1_NODES_PATH = REPO_ROOT / "data" / "act1_nodes.json"
LOG_PATH = REPO_ROOT / "logs" / "evolve.log"
BUILD_SCRIPT = REPO_ROOT / "build_frontend.py"

# ── API Config ─────────────────────────────────────────────────
KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-8k"

# ── Act 1 archetype paths (choice chains) ──────────────────────
ARCHETYPE_PATHS = {
    "person_present": ["1.0", "2.1", "3.0", "4.1", "5.1", "6.1", "7.0", "8.0", "9.1", "10.0"],
    "person_gone":    ["1.0", "2.1", "3.0", "4.1", "5.2", "6.2", "7.0", "8.0", "9.1", "10.0"],
    "self_regret":    ["1.0", "2.2", "3.0", "4.2", "5.3", "6.3", "7.0", "8.0", "9.2", "10.0"],
    "self_unlived":   ["1.0", "2.2", "3.0", "4.2", "5.4", "6.4", "7.0", "8.0", "9.2", "10.0"],
}


def get_api_key() -> str:
    """Resolve Moonshot API key from env or ~/.hermes/.env"""
    key = os.environ.get("MOONSHOT_API_KEY", "")
    if key:
        return key
    env_path = Path.home() / ".hermes" / ".env"
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.startswith("KIMI_API_KEY="):
                    return line.strip().split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("No MOONSHOT_API_KEY found in env or ~/.hermes/.env")


def kimi_chat(messages: list, max_tokens: int = 300, temperature: float = 0.9) -> str:
    """Call Kimi chat completions endpoint."""
    key = get_api_key()
    payload = {
        "model": KIMI_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    req = urllib.request.Request(
        f"{KIMI_BASE_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


def log(msg: str) -> None:
    ts = datetime.datetime.now().isoformat()
    line = f"[{ts}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_voice_rules() -> str:
    with open(VOYD_SYSTEM_MD, encoding="utf-8") as f:
        return f.read()


def simulate_act1() -> dict:
    """Walk a random archetype path through Act 1 and return final state."""
    with open(ACT1_NODES_PATH, encoding="utf-8") as f:
        data = json.load(f)
    nodes = data["nodes"]

    archetype = random.choice(list(ARCHETYPE_PATHS.keys()))
    path = ARCHETYPE_PATHS[archetype]
    portal_value = 8

    log(f"Simulating Act 1 — archetype: {archetype}")

    for node_id in path:
        node = nodes[node_id]
        if node.get("choices"):
            choice = random.choice(node["choices"])
            portal_value = max(0, min(100, portal_value + choice.get("delta", 0)))

    final_node = nodes["10.0"]
    log(f"Act 1 complete — portal_value: {portal_value}, archetype: {archetype}")

    return {
        "archetype": archetype,
        "portal_value": portal_value,
        "path": path,
        "final_node_text": final_node["text"],
    }


def generate_player_answer(state: dict) -> str:
    """Use Kimi to generate a raw human answer at node 10.0."""
    voice = load_voice_rules()
    final_text = state['final_node_text']
    prompt = (
        f"{voice}\n\n"
        f"You are simulating a human player who has just completed Act 1 of a narrative game.\n"
        f"Their archetype is: {state['archetype']}\n"
        f"Their portal value is: {state['portal_value']}\n\n"
        f"The final node text they read was:\n"
        f"{final_text}\n\n"
        f'The prompt asked: "what is different about it?" referring to the parallel version of their life.\n\n'
        f"Generate a SHORT, plausible human answer (1-2 sentences, emotional, raw, lowercase).\n"
        f"Do not use em dashes. Keep it under 30 words."
    )
    answer = kimi_chat([{"role": "user", "content": prompt}], max_tokens=60, temperature=0.95)
    answer = answer.strip().lower().replace("—", " ")
    log(f"Generated player answer: {answer[:120]}")
    return answer


def generate_act2_nodes(state: dict, player_answer: str) -> list:
    """Generate 3 Voyd response texts for Act 2 via Kimi."""
    voice = load_voice_rules()
    prompt = textwrap.dedent(f"""\
        {voice}

        The player has completed Act 1. Their profile:
        - Archetype: {state['archetype']}
        - Portal value entering Act 2: {state['portal_value']}
        - They named: "{player_answer}"

        Generate 3 distinct Voyd responses. Each response must:
        - Be 2-4 sentences
        - Be entirely lowercase (except proper names that drift)
        - Never begin with "I"
        - Never use em dashes
        - Feel like a dreaming dimension speaking, not a person
        - Be compressed, slightly wrong, drifting names
        - Not answer directly — gesture, image, feeling

        Format exactly as:
        RESPONSE 1:
        [text]

        RESPONSE 2:
        [text]

        RESPONSE 3:
        [text]
    """)
    raw = kimi_chat([{"role": "user", "content": prompt}], max_tokens=500, temperature=0.95)
    log(f"Raw generation received ({len(raw)} chars)")

    responses = []
    for i in range(1, 4):
        marker = f"RESPONSE {i}:"
        start = raw.find(marker)
        if start == -1:
            log(f"Warning: could not find {marker}")
            continue
        start += len(marker)
        end_marker = f"RESPONSE {i + 1}:"
        end = raw.find(end_marker) if i < 3 else len(raw)
        text = raw[start:end].strip()
        text = text.replace("—", " ").replace("  ", " ").strip()
        if text:
            responses.append(text)

    return responses


def score_node(text: str) -> dict:
    """Score generated text on voice, polarity, momentum. Promote if total >= 21."""
    # ── Voice (0-10) ────────────────────────────────────────────
    voice_score = 5
    if text == text.lower():
        voice_score += 2
    if not text.startswith("i"):
        voice_score += 2
    if "—" not in text:
        voice_score += 1
    sentences = [s for s in text.split(".") if s.strip()]
    if 2 <= len(sentences) <= 5:
        voice_score += 1
    voice_score = min(10, max(0, voice_score))

    # ── Polarity (0-10) ─────────────────────────────────────────
    polarity_score = 5
    intense = {"grief", "loss", "want", "hunger", "dark", "silence", "fall", "depth",
               "void", "dream", "pain", "need", "fear", "longing", "weight", "sorrow"}
    polarity_score += sum(1 for w in intense if w in text)
    polarity_score = min(10, max(0, polarity_score))

    # ── Momentum (0-10) ─────────────────────────────────────────
    momentum_score = 5
    forward = {"reach", "fall", "pull", "open", "become", "listen", "wait", "come",
               "step", "pass", "move", "turn", "bend", "flow", "drift", "rise"}
    momentum_score += sum(1 for w in forward if w in text)
    momentum_score = min(10, max(0, momentum_score))

    total = voice_score + polarity_score + momentum_score
    return {
        "voice": voice_score,
        "polarity": polarity_score,
        "momentum": momentum_score,
        "total": total,
        "promoted": total >= 21,
    }


def main():
    log("=" * 50)
    log("evolve.py starting")

    with open(ACT1_NODES_PATH, encoding="utf-8") as f:
        data = json.load(f)

    # ── 1-3: Simulate Act 1 ─────────────────────────────────────
    state = simulate_act1()

    # ── 4: Generate player answer at node 10.0 ──────────────────
    player_answer = generate_player_answer(state)

    # ── 5: Generate 3 Act 2 nodes ───────────────────────────────
    responses = generate_act2_nodes(state, player_answer)
    if not responses:
        log("ERROR: No responses generated")
        sys.exit(1)

    # ── 6: Score and promote ────────────────────────────────────
    promoted = 0
    existing_ids = set(data["nodes"].keys())
    gen_num = 1
    while f"gen_{gen_num}" in existing_ids:
        gen_num += 1

    for text in responses:
        score = score_node(text)
        log(
            f"Node gen_{gen_num}: voice={score['voice']}, polarity={score['polarity']}, "
            f"momentum={score['momentum']}, total={score['total']}, promoted={score['promoted']}"
        )

        if score["promoted"]:
            promoted += 1
            gen_id = f"gen_{gen_num}"
            data["nodes"][gen_id] = {
                "id": gen_id,
                "label": f"generated_{gen_num}",
                "text": text,
                "delta": 0,
                "choices": [],
                "source": "generated",
                "score": score,
            }
            log(f"Promoted {gen_id}: {text[:100]}...")
            gen_num += 1

    # ── Update meta ─────────────────────────────────────────────
    data["meta"]["last_evolved"] = datetime.datetime.now().isoformat()
    data["meta"]["total_sessions"] = data["meta"].get("total_sessions", 0) + 1
    data["meta"]["promoted_nodes"] = data["meta"].get("promoted_nodes", 0) + promoted

    # ── Save ────────────────────────────────────────────────────
    with open(ACT1_NODES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    log(f"Saved {ACT1_NODES_PATH}")

    # ── 8: Run build_frontend.py ────────────────────────────────
    try:
        subprocess.run([sys.executable, str(BUILD_SCRIPT)], check=True, cwd=REPO_ROOT)
        log("build_frontend.py completed")
    except subprocess.CalledProcessError as e:
        log(f"build_frontend.py failed: {e}")
        sys.exit(1)

    log(f"Evolution complete. Promoted {promoted} / {len(responses)} nodes.")
    log("=" * 50)


if __name__ == "__main__":
    main()
