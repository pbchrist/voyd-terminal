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


PATHS = {
    "demanded_identity": ["1.0", "2.1", "revelation.di", "threshold.di", "ACT2"],
    "claimed_knowledge": ["1.0", "2.1", "revelation.ck", "threshold.ck", "ACT2"],
    "demanded_motive": ["1.0", "2.2", "revelation.dm", "threshold.dm", "ACT2"],
    "identity_as_bait": ["1.0", "2.2", "revelation.ib", "threshold.ib", "ACT2"],
}


def finish_variant(route: str, variant: str) -> dict:
    state = headless_play.revelation_state(route)
    if variant == "withdraw":
        return headless_play.apply_handoff_action(state, "withdraw")
    state = headless_play.apply_handoff_action(state, "seek_change")
    if variant == "pending":
        return state
    if variant == "declined":
        return headless_play.capture_petition(state, "nothing")
    if variant == "reframe_required":
        return headless_play.capture_petition(state, "take me back and retrieve the person i lost")
    state = headless_play.capture_petition(
        state, "repair my present promise with my friend")
    state = headless_play.reveal_counterforce(state)
    state = headless_play.offer_terms(state)
    if variant == "refused":
        return headless_play.resolve_offer(state, "refuse")
    state = headless_play.resolve_offer(state, "accept")
    if variant == "fulfilled":
        return headless_play.resolve_obligation(state, state["fulfillment_action"])
    if variant == "breached":
        return headless_play.resolve_obligation(state, state["breach_action"])
    return state


def build_packet() -> dict:
    act1 = json.loads((ROOT / "data" / "act1_nodes.json").read_text(encoding="utf-8"))
    walks = []
    for route in ROUTES:
        for variant in ("withdraw", "pending", "declined", "reframe_required", "accepted", "refused", "fulfilled", "breached"):
            handoff = finish_variant(route, variant)
            path = PATHS[route]
            walks.append({
                "route": route,
                "resolution_variant": variant,
                "path": path,
                "node_texts": [act1["nodes"][node]["text"] for node in path if node in act1["nodes"]],
                "choices": list(handoff["choice_history"]),
                "handoff": handoff,
                "act2_opening": headless_play.handoff_opening(handoff),
                "act2_prompt": headless_play.build_act2_prompt(None, "", 8, handoff),
                "final_portal_value": 8,
                "player_answer": "",
            })

    classifier_inputs = {
        "nothing": "petition_declined",
        "take me back and retrieve the person i lost": "petition_reframe_required",
        "keep my present promise with my friend": "petition_validated",
        "go back forty years": "petition_reframe_required",
    }
    adversarial_classifier_cases = []
    for route in ROUTES:
        pending = headless_play.apply_handoff_action(
            headless_play.revelation_state(route), "seek_change")
        for text, expected in classifier_inputs.items():
            adversarial_classifier_cases.append({
                "route": route,
                "input": text,
                "expected_lifecycle": expected,
                "handoff": headless_play.capture_petition(pending, text),
            })

    return {
        "schema_version": 2,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repository": str(ROOT),
        "selected_structural_species": act1.get("meta", {}).get("structural_species"),
        "purpose": "Authoritative model-free story packet for all Phantom Walkers in one room cycle.",
        "adversarial_classifier_cases": adversarial_classifier_cases,
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
