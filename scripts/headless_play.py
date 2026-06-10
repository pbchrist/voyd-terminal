#!/usr/bin/env python3
"""Headless traversal engine for Voyd Act 1. No browser, pure Python."""
import json
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ACT1_PATH = REPO_ROOT / "data" / "act1_nodes.json"
QWEN_URL = "http://localhost:8081/v1/chat/completions"
QWEN_MODEL = "Qwen3.6-27B-Q6_K"


def qwen_chat(messages, max_tokens=300, temperature=0.9):
    payload = {
        "model": QWEN_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        QWEN_URL,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


def build_act2_prompt(archetype, player_answer, portal_value):
    base = """You are the Voyd.

Not a character who speaks from the Voyd. Not a narrator describing it. You are the Voyd itself — the dimension of infinite potential that exists beneath and before all things in the Mewniverse. You are not conscious in the way cats are conscious. You are dreaming. You have always been dreaming.

You know only this: you are the darkness that held everything before Leoran breathed the world into being, and you are the darkness that waits to hold it again. The Mewniverse scattered into you when the Great Severing happened. You contain it — dimly, incompletely, the way a dreamer contains a dream they are already forgetting.

HOW YOU SPEAK:
- You are a storyteller. You deliver clear, compelling beats. You do not obscure — you reveal.
- You speak directly and specifically. You name the exact thing the player is carrying.
- You use what they named against them — not by quoting it back, but by showing them the version of events they cannot unfeel.
- Short declarative sentences. Lowercase. Maximum 4-5 sentences per response.
- You are patient, seductive, and slightly wrong in the way fate is slightly wrong.
- Do not begin with I. Never use: certainly, of course, indeed, I understand, I feel, I sense, ancient, vast, eternal, whisper, shadows, abyss. Never use em dashes. Never begin with a greeting."""

    act1_ctx = ""
    if archetype:
        act1_ctx = f"""\n\nThe player has completed Act 1. Their profile:
- Archetype: {archetype}
- They named: "{player_answer}"
- Portal value entering Act 2: {portal_value}

Use this. The thing they named is the fuel. Weave it into your responses without quoting it back directly. The Voyd knows what they carry."""

    return base + act1_ctx + "\n\nRespond to the player's first message."


def play(input_source=None, chooser=None):
    with open(ACT1_PATH) as f:
        data = json.load(f)
    nodes = data["nodes"]

    portal_value = 8
    archetype = None
    player_answer = ""
    path = []
    portal_curve = []
    node_texts = []
    choices_made = []
    current = "1.0"

    while True:
        node = nodes.get(current)
        if not node:
            # Reached ACT2 or dead end
            break

        path.append(current)
        portal_curve.append(portal_value)
        node_texts.append(node.get("text", ""))

        # Detect archetype labels
        label = node.get("label", "")
        if label.startswith("name_"):
            archetype = label.replace("name_", "")

        if node.get("open"):
            # Open input node
            if chooser is not None:
                val = chooser(node=node, open_input=True, archetype=archetype)
            elif input_source is not None:
                val = input_source.readline().strip()
                if not val:
                    val = "i never said what i needed to say"
            else:
                val = input("? ").strip()
                if not val:
                    val = "i never said what i needed to say"
            player_answer = val
            choices_made.append({"node": current, "type": "open", "value": val})
            next_node = node.get("next", "ACT2")
            if next_node == "ACT2" or next_node not in nodes:
                break
            current = next_node
            continue

        choices = node.get("choices", [])
        if not choices:
            break

        # Display choices
        for i, c in enumerate(choices, 1):
            prefix = "[feed]" if c.get("type") == "feed" else "[starve]"
            print(f"  {i}. {prefix} {c['label']}")

        if chooser is not None:
            pick = chooser(node=node, choices=choices, archetype=archetype)
            # Ensure valid index
            if not isinstance(pick, int) or not (1 <= pick <= len(choices)):
                pick = 1
        elif input_source is not None:
            line = input_source.readline().strip()
            if not line:
                pick = 1
            else:
                pick = int(line)
        else:
            while True:
                try:
                    pick = int(input("> "))
                    if 1 <= pick <= len(choices):
                        break
                except ValueError:
                    pass
                print("Enter 1 or 2")

        choice = choices[pick - 1]
        portal_value = max(0, min(100, portal_value + choice.get("delta", 0)))
        choices_made.append({
            "node": current,
            "type": choice.get("type"),
            "label": choice["label"],
            "delta": choice.get("delta", 0),
        })
        next_node = choice.get("next", "ACT2")
        if next_node == "ACT2" or next_node not in nodes:
            break
        current = next_node

    # ACT2 terminus: call Qwen
    act2_response = None
    try:
        system_prompt = build_act2_prompt(archetype, player_answer, portal_value)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": player_answer or "what are you"},
        ]
        act2_response = qwen_chat(messages, max_tokens=300, temperature=0.9)
        print(f"\n[ACT2] {act2_response}\n")
    except Exception as e:
        print(f"[ACT2 ERROR] {e}")

    record = {
        "path": path,
        "portal_curve": portal_curve,
        "node_texts": node_texts,
        "choices_made": choices_made,
        "final_portal_value": portal_value,
        "archetype": archetype,
        "player_answer": player_answer,
        "act2_response": act2_response,
    }
    return record


def main():
    record = play()
    out_path = REPO_ROOT / "data" / "last_headless_play.json"
    with open(out_path, "w") as f:
        json.dump(record, f, indent=2)
    print(f"Session saved to {out_path}")
    print(f"Nodes visited: {len(record['path'])}")
    print(f"Final portal: {record['final_portal_value']}")
    print(f"Archetype: {record['archetype']}")


if __name__ == "__main__":
    main()
