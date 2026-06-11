#!/usr/bin/env python3
"""Rewrite a promoted node's prose in place, gated by the dramaturg.

Usage: python3 scripts/rewrite_node.py <node_id> [max_attempts]

For beats the phantom reader-judge repeatedly flags as weakest: regenerate the
experienced surface (text, seed, choice labels) from the node's own canon event
— the generator now sees the reader complaints — and accept only a draft the
dramaturg scores at or above the auto-promote threshold. The node's place in
the graph is untouched: id, choice targets, act, tension_delta, dialectic_role.
"""
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

spec = importlib.util.spec_from_file_location("evolve", REPO_ROOT / "evolve.py")
evolve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evolve)


def rewrite(node_id: str, max_attempts: int = 4) -> bool:
    state = evolve.load_state(REPO_ROOT)
    nodes = state["act1_nodes"]["nodes"]
    node = nodes.get(node_id)
    if node is None:
        print(f"[rewrite] no such node: {node_id}")
        return False
    event = next((e for e in state["canon_events"] if e["id"] == node.get("canon_event")), None)
    if event is None:
        print(f"[rewrite] node {node_id} has no canon event; cannot regenerate")
        return False

    threshold = state["rubric"].get("auto_promote_threshold", 24)
    old_score = (node.get("score") or {}).get("total", (node.get("score") or {}).get("score"))

    # Judge the rewrite at its real position: its graph predecessors are the scenes
    # the reader just lived through, not the current frontier (which may sit after it).
    predecessors = [
        n for nid, n in nodes.items()
        if any(c.get("next") == node_id for c in n.get("choices", []))
        or n.get("next") == node_id
        or node_id in (n.get("next_archetype") or {}).values()
    ][:3]

    for attempt in range(1, max_attempts + 1):
        candidate = evolve.generate_node(state, event)
        score = evolve.score_node(candidate, state["rubric"], state["act1_nodes"],
                                  context_nodes=predecessors or None)
        print(f"[rewrite] attempt {attempt}: {score['total']}/30 — {score['reason'][:120]}")
        if score["decision"] != "promote":
            continue

        # Keep the graph identical: new choice labels inherit the old targets by type.
        old_next = {c.get("type"): c.get("next") for c in node.get("choices", [])}
        fallback = next(iter(old_next.values()), "ACT2")
        for choice in candidate["choices"]:
            choice["next"] = old_next.get(choice.get("type"), fallback)

        node["text"] = candidate["text"]
        node["seed"] = candidate["seed"]
        node["choices"] = candidate["choices"]
        node["score"] = {k: v for k, v in score.items() if k != "raw"}
        node["rewritten_at"] = datetime.now().isoformat()

        evolve.record_decision(state["rubric"], {
            "at": node["rewritten_at"],
            "canon_event": event["id"],
            "node_id": node_id,
            "score": score,
            "decision": "rewrite",
            "reason": "reader-judge repeatedly flagged this beat as weakest; prose regenerated in place",
        })
        evolve.write_json(evolve.ACT1_NODES_PATH, state["act1_nodes"])
        evolve.write_json(evolve.RUBRIC_PATH, state["rubric"])
        evolve.run_build(REPO_ROOT)

        evolve.send_telegram_text(
            f"✍️ Rewrote {node_id} in place (was {old_score}, now {score['total']}/30). "
            f"Readers kept flagging it as the weakest beat.\n“{node['text'][:250]}”"
        )
        print(f"[rewrite] {node_id} rewritten (dramaturg {score['total']}/30)")
        return True

    print(f"[rewrite] no draft reached {threshold}/30 in {max_attempts} attempts; {node_id} unchanged")
    return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    attempts = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    raise SystemExit(0 if rewrite(sys.argv[1], attempts) else 1)
