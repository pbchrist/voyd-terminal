#!/usr/bin/env python3
"""Autonomous player that traverses Voyd Act 1 via LLM decisions."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from headless_play import play, qwen_chat

VALID_ARCHETYPES = {"person_present", "person_gone", "self_regret", "self_unlived"}


ARCHETYPE_ROUTING = {
    "1.0": {"person_present": 1, "person_gone": 1, "self_regret": 2, "self_unlived": 2},
    "3.0": {"person_present": 1, "person_gone": 1, "self_regret": 2, "self_unlived": 2},
    "4.1": {"person_present": 1, "person_gone": 2},
    "4.2": {"self_regret": 1, "self_unlived": 2},
}


def make_chooser(target_archetype):
    def chooser(node=None, choices=None, open_input=False, archetype=None):
        effective = archetype or target_archetype
        if open_input:
            prompt = (
                f"You are roleplaying a person with the archetype '{effective}'.\n"
                f"The Voyd asks:\n{node.get('text', '')}\n\n"
                f"Respond with a single raw answer this person would give. "
                f"No quotes, no explanation, just the answer."
            )
            messages = [{"role": "user", "content": prompt}]
            return qwen_chat(messages, max_tokens=60, temperature=0.9).strip().strip('"').strip("'")

        node_id = node.get("id", "")
        # Enforce archetype routing at critical authored nodes
        if node_id in ARCHETYPE_ROUTING and effective in ARCHETYPE_ROUTING[node_id]:
            return ARCHETYPE_ROUTING[node_id][effective]

        # Choice node — use LLM for non-critical nodes and epilogues
        choice_text = "\n".join(
            f"{i}. [{c.get('type', '')}] {c['label']}" for i, c in enumerate(choices, 1)
        )
        prompt = (
            f"You are roleplaying a person with the archetype '{effective}'.\n"
            f"The Voyd says:\n{node.get('text', '')}\n\n"
            f"Choose the option most consistent with this archetype:\n{choice_text}\n\n"
            f"Respond with ONLY the number 1 or 2. No explanation."
        )
        messages = [{"role": "user", "content": prompt}]
        raw = qwen_chat(messages, max_tokens=10, temperature=0.7).strip()
        # Extract first digit
        for ch in raw:
            if ch in "12":
                return int(ch)
        return 1

    return chooser


def run(archetype, out_path=None, act1_data=None):
    if archetype not in VALID_ARCHETYPES:
        raise ValueError(f"Invalid archetype: {archetype}. Must be one of {VALID_ARCHETYPES}")
    print(f"[llm_play] Starting walk for archetype: {archetype}")
    record = play(chooser=make_chooser(archetype), act1_data=act1_data)
    record["archetype"] = archetype
    if out_path:
        with open(out_path, "w") as f:
            json.dump(record, f, indent=2)
        print(f"[llm_play] Saved to {out_path}")
    print(f"[llm_play] Nodes: {len(record['path'])}, Final portal: {record['final_portal_value']}")
    return record


def main():
    parser = argparse.ArgumentParser(description="Autonomous Voyd Act 1 player")
    parser.add_argument("archetype", choices=sorted(VALID_ARCHETYPES))
    parser.add_argument("--out", "-o", help="Output JSON path")
    args = parser.parse_args()
    run(args.archetype, out_path=args.out)


if __name__ == "__main__":
    main()
