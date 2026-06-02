#!/usr/bin/env python3
"""
Build script: generates frontend data files from the narrative engine.
Outputs static JSON that the frontend loads.
"""
import json
import shutil
from pathlib import Path

# Load story graph
with open("data/story_graph.json") as f:
    graph = json.load(f)

# Load lore index chunks by topic
from engine.lore_index import get_index
index = get_index()

# Build compact topic → chunks map
lore_map = {}
for topic in graph["intent_map"]["keywords"].keys():
    chunks = index.query([topic], max_results=3)
    lore_map[topic] = chunks

# Also include general fallback
lore_map["general"] = index.query(["voyd_entity", "mewniverse"], max_results=3)

# Write compact data file
output = {
    "meta": graph["meta"],
    "nodes": graph["nodes"],
    "intent_map": graph["intent_map"],
    "lore_map": lore_map,
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
