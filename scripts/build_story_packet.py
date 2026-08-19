#!/usr/bin/env python3
"""Build one deterministic, model-free play packet for Phantom Walker review."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import headless_play  # type: ignore

ROUTES = {
    "demanded_identity": (1, 1),
    "claimed_knowledge": (1, 2),
    "demanded_motive": (2, 2),
    "identity_as_bait": (2, 1),
}


def chooser(entry: int, opening: int, later: int):
    def choose(*, node, choices=None, open_input=False, **_):
        if open_input:
            return "the future i am choosing now"
        if node["id"] == "1.0":
            return entry
        if node["id"] in {"2.1", "2.2"}:
            return opening
        return later
    return choose


def build_packet() -> dict:
    act1 = json.loads((ROOT / "data" / "act1_nodes.json").read_text(encoding="utf-8"))
    original_qwen = headless_play.qwen_chat
    headless_play.qwen_chat = lambda *_args, **_kwargs: "[MODEL-FREE PACKET: ACT2 RESPONSE OMITTED]"
    try:
        walks = []
        for identity, (entry, opening) in ROUTES.items():
            for later, outcome_label in ((1, "primary_resolution"), (2, "counter_resolution")):
                record = headless_play.play(
                    chooser=chooser(entry, opening, later),
                    act1_data=act1,
                )
                walks.append({
                    "route": identity,
                    "resolution_variant": outcome_label,
                    "path": record["path"],
                    "node_texts": record["node_texts"],
                    "choices": record.get("choices", []),
                    "contract": record["contract"],
                    "act2_opening": record["act2_opening"],
                    "act2_prompt": record["act2_prompt"],
                    "final_portal_value": record["final_portal_value"],
                    "player_answer": record["player_answer"],
                })
    finally:
        headless_play.qwen_chat = original_qwen

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": str(ROOT),
        "selected_structural_species": act1.get("meta", {}).get("structural_species"),
        "purpose": "Authoritative model-free story packet for all Phantom Walkers in one room cycle.",
        "walks": walks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output
    if output is None:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        output = ROOT / "story_room" / "packets" / f"{stamp}.json"
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_packet(), indent=2) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
