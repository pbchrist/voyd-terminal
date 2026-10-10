#!/usr/bin/env python3
"""
Build script: generates frontend data files from the narrative engine.
Outputs static JSON that the frontend loads.
"""
import json
import shutil
from pathlib import Path

SPECIES = "mutation_revelation_threshold_then_live_bargain"
LIFECYCLES = {
    "unbound_closed", "petition_pending", "petition_declined",
    "petition_reframe_required", "petition_validated", "counterforce_revealed",
    "terms_offered", "accepted_with_obligation", "refused", "fulfilled", "breached",
}


def validate_sources(graph, act1):
    """Reject incomplete generated data before it reaches the browser."""
    if act1.get("meta", {}).get("structural_species") != SPECIES:
        raise ValueError(f"expected selected structural species {SPECIES}")
    nodes = act1.get("nodes", {})
    starts = nodes.get("2.1", {}).get("choices", []) + nodes.get("2.2", {}).get("choices", [])
    if len(starts) != 4:
        raise ValueError("live-bargain Act 1 must expose four revelation routes")
    revelation_ids = set()
    for choice in starts:
        seed = choice.get("handoff_start", {})
        required = ("revelation_id", "revelation_text", "terms_constraint")
        if seed.get("lifecycle") != "revelation_only" or not all(seed.get(k) for k in required):
            raise ValueError("each Act 1 route must earn a constrained revelation")
        if seed.get("contract_identity") is not None or seed.get("unpaid_cost") is not None:
            raise ValueError("contract identity and leverage cannot exist before terms")
        revelation_ids.add(seed["revelation_id"])
    if len(revelation_ids) != 4:
        raise ValueError("the four revelation routes must remain distinct")

    entries = graph.get("meta", {}).get("handoff_entries", {})
    missing = LIFECYCLES - set(entries)
    unresolved = {life: node for life, node in entries.items() if node not in graph.get("nodes", {})}
    if missing or unresolved:
        raise ValueError(f"unsafe handoff entries; missing={sorted(missing)}, unresolved={unresolved}")

# Load story graph
with open("data/story_graph.json") as f:
    graph = json.load(f)
with open("data/act1_nodes.json") as f:
    act1 = json.load(f)
validate_sources(graph, act1)

# Load lore index chunks by topic
from engine.lore_index import get_index
index = get_index()

# Build compact topic → chunks map, keyed by the lore_context names the
# client-side engine actually queries at runtime.
lore_topics = set()
for node in graph["nodes"].values():
    lore_topics.update(node.get("lore_context", []))

lore_map = {}
for topic in sorted(lore_topics):
    chunks = index.query([topic], max_results=3)
    if chunks:
        lore_map[topic] = chunks

# Also include general fallback
lore_map["general"] = index.query(["voyd_entity", "mewniverse"], max_results=3)

# The Voyd voice prompt has a single source of truth: data/voyd_system.md
voice_prompt = Path("data/voyd_system.md").read_text(encoding="utf-8").strip()

# Write compact data file
output = {
    "meta": graph["meta"],
    "nodes": graph["nodes"],
    "intent_map": graph["intent_map"],
    "lore_map": lore_map,
    "voice_prompt": voice_prompt,
}

out_path = Path("frontend/voyd_data.json")
with open(out_path, "w") as f:
    json.dump(output, f, separators=(',', ':'))

print(f"Built {out_path}: {out_path.stat().st_size} bytes")
print(f"Nodes: {len(graph['nodes'])}, Lore topics: {len(lore_map)}")

# Copy act1_nodes.json to frontend data directory
act1_src = Path("data/act1_nodes.json")
act1_dst_dir = Path("frontend/data")
act1_dst_dir.mkdir(exist_ok=True)
act1_dst = act1_dst_dir / "act1_nodes.json"
shutil.copy2(act1_src, act1_dst)
print(f"Copied {act1_src} -> {act1_dst}")
