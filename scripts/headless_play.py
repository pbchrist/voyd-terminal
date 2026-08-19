#!/usr/bin/env python3
"""Headless traversal engine for Voyd Act 1. No browser, pure Python."""
import json
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ACT1_PATH = REPO_ROOT / "data" / "act1_nodes.json"
VOICE_PATH = REPO_ROOT / "data" / "voyd_system.md"
QWEN_URL = "http://localhost:8081/v1/chat/completions"
QWEN_MODEL = "Qwen3.6-27B-Q6_K"


def load_voice_prompt():
    """The Voyd voice prompt has a single source of truth: data/voyd_system.md."""
    try:
        return VOICE_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return ("You are the Voyd. Speak in short, lowercase, declarative sentences. "
                "Maximum 4-5 sentences per response.")


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


CONTRACT_FIELDS = (
    "identity", "terms", "initiative", "resolution", "unpaid_cost",
    "choice_history", "personal_referent", "exposed_risk",
    "reciprocal_demand", "explicit_test",
)


def create_contract_state(seed=None):
    """Create the semantic contract state shared with frontend/contract_state.js."""
    state = {
        "identity": None,
        "terms": [],
        "initiative": "player",
        "resolution": "unformed",
        "unpaid_cost": None,
        "choice_history": [],
        "personal_referent": None,
        "exposed_risk": None,
        "reciprocal_demand": None,
        "explicit_test": None,
    }
    for field in CONTRACT_FIELDS:
        if seed and field in seed:
            value = seed[field]
            state[field] = list(value) if isinstance(value, list) else value
    return state


def apply_contract_choice(current, choice):
    """Apply a data-authored contract start/update and append its action history."""
    state = create_contract_state(choice.get("contract_start") or current)
    for field, value in (choice.get("contract_update") or {}).items():
        if field in CONTRACT_FIELDS and field != "choice_history":
            state[field] = list(value) if isinstance(value, list) else value
    action = choice.get("contract_action")
    if action:
        state["choice_history"].append(action)
    return state


def contract_prompt_context(contract):
    if not contract or not contract.get("identity"):
        return ""
    terms = " | ".join(contract["terms"]) if contract["terms"] else "none"
    history = " -> ".join(contract["choice_history"]) if contract["choice_history"] else "none"
    return (
        f"\n- Active contract: {contract['identity']}"
        f"\n- Contract terms: {terms}"
        f"\n- Initiative: {contract['initiative']}"
        f"\n- Resolution: {contract['resolution']}"
        f"\n- Unpaid cost: {contract['unpaid_cost'] or 'none'}"
        f"\n- Choice history: {history}"
        f"\n- Personal referent: {contract['personal_referent'] or 'undisclosed'}"
        f"\n- Voyd risk exposed: {contract['exposed_risk'] or 'none'}"
        f"\n- Reciprocal demand: {contract['reciprocal_demand'] or 'none'}"
        f"\n- Test already performed: {contract['explicit_test'] or 'none'}"
    )


def contract_opening(contract):
    """Deterministic first Act 2 counterstroke used when live generation is absent."""
    if not contract or not contract.get("identity"):
        return ""
    name = contract["identity"].replace("_", " ")
    subject = contract["personal_referent"] or "chosen subject"
    opening = (
        f"the {name} contract enters before your question. "
        f"it ended {contract['resolution']}, with {contract['initiative']} holding initiative over {subject}. "
    )
    if contract["unpaid_cost"]:
        return opening + f"the unpaid cost is still exact: {contract['unpaid_cost']}. answer from inside that consequence."
    return opening + "nothing unpaid survives, so i will not invent a new debt. answer from the consequence you chose."


def build_act2_prompt(archetype, player_answer, portal_value, contract=None):
    base = load_voice_prompt()

    act1_ctx = ""
    if archetype:
        act1_ctx = f"""\n\nThe player has completed Act 1. Their profile:
- Archetype: {archetype}
- They named: "{player_answer}"
- Portal value entering Act 2: {portal_value}{contract_prompt_context(contract)}

The contract is operative, not profile flavor. Your first return must enforce its resolution, honor what you owe, or collect its exact unpaid cost. Do not replace it with neutral profiling. The named referent remains the subject unless the player changes it by action."""

    return base + act1_ctx + "\n\nRespond to the player's first message."


def play(input_source=None, chooser=None, act1_data=None):
    if act1_data is None:
        with open(ACT1_PATH) as f:
            act1_data = json.load(f)
    nodes = act1_data["nodes"]

    portal_value = 8
    archetype = None
    player_answer = ""
    path = []
    portal_curve = []
    node_texts = []
    choices_made = []
    contract = create_contract_state()
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
            if node.get("next_archetype") and archetype and archetype in node["next_archetype"]:
                next_node = node["next_archetype"][archetype]
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
        contract = apply_contract_choice(contract, choice)
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
    system_prompt = build_act2_prompt(archetype, player_answer, portal_value, contract)
    try:
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
        "contract": contract,
        "act2_prompt": system_prompt,
        "act2_opening": contract_opening(contract),
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
