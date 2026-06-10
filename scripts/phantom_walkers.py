#!/usr/bin/env python3
"""Phantom Walkers: simulate all four archetypes and score the combined experience."""
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from llm_play import run as llm_run

REPO_ROOT = Path(__file__).parent.parent
WALK_SCORES_PATH = REPO_ROOT / "data" / "walk_scores.json"
STORY_MAP_PATH = REPO_ROOT / "data" / "story_map.json"
ENV_PATH = Path.home() / ".hermes" / ".env"

ARCHETYPES = ["person_present", "person_gone", "self_regret", "self_unlived"]


def load_env():
    env = {}
    if ENV_PATH.exists():
        with open(ENV_PATH) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k] = v.strip('"').strip("'")
    return env


def load_story_map():
    with open(STORY_MAP_PATH) as f:
        return json.load(f)


def jaccard_similarity(set_a, set_b):
    if not set_a and not set_b:
        return 1.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union else 0.0


def score_walk(walk, all_walks, story_map):
    path = walk["path"]
    nodes = story_map.get("nodes", {})

    # Dialectic arc: count decreases or flat for 2+ consecutive nodes
    deltas = [nodes.get(n, {}).get("tension_delta", 0) for n in path]
    flat_runs = 0
    current_run = 0
    for d in deltas:
        if d <= 0:
            current_run += 1
        else:
            if current_run >= 2:
                flat_runs += 1
            current_run = 0
    if current_run >= 2:
        flat_runs += 1
    dialectic_arc = max(0, 10 - flat_runs * 2)

    # Path uniqueness: Jaccard against most similar other walk
    my_set = set(path)
    best_sim = 0.0
    for other in all_walks:
        if other is walk:
            continue
        other_set = set(other["path"])
        sim = jaccard_similarity(my_set, other_set)
        if sim > best_sim:
            best_sim = sim
    path_uniqueness = round(10 * (1 - best_sim), 2)

    # Cathartic potential: choke within 15 nodes?
    choke_within_15 = False
    for i, nid in enumerate(path[:15], 1):
        if nodes.get(nid, {}).get("type") == "choke":
            choke_within_15 = True
            break

    # Also check if it reaches ACT2 (path ends with a node whose next is ACT2 or not in act1)
    reached_act2 = walk.get("act2_response") is not None

    if choke_within_15:
        cathartic_potential = 10
    elif reached_act2:
        cathartic_potential = 5
    else:
        cathartic_potential = 0

    return {
        "dialectic_arc": dialectic_arc,
        "path_uniqueness": path_uniqueness,
        "cathartic_potential": cathartic_potential,
    }


def find_kills(walks):
    """Kill nodes that appear in all 4 walks with identical downstream sequences."""
    if len(walks) < 4:
        return []

    paths = [w["path"] for w in walks]
    # Find nodes common to all paths
    common = set(paths[0])
    for p in paths[1:]:
        common &= set(p)

    kills = []
    for node in common:
        # Get downstream sequences from this node for each walk
        suffixes = []
        for p in paths:
            idx = p.index(node)
            suffixes.append(tuple(p[idx:]))

        if len(set(suffixes)) == 1:
            # All identical downstream
            kills.append(node)

    return kills


def find_flags(walks, story_map):
    """Flag walks with no tension increase for 3+ consecutive nodes."""
    flags = []
    nodes = story_map.get("nodes", {})
    for walk in walks:
        path = walk["path"]
        deltas = [nodes.get(n, {}).get("tension_delta", 0) for n in path]
        run_start = None
        for i, d in enumerate(deltas):
            if d <= 0:
                if run_start is None:
                    run_start = i
            else:
                if run_start is not None and i - run_start >= 3:
                    seg = "-".join(path[run_start:i])
                    flags.append(f"{path[run_start]}-{path[i-1]} flat in {walk['archetype']} walk")
                run_start = None
        if run_start is not None and len(deltas) - run_start >= 3:
            flags.append(f"{path[run_start]}-{path[-1]} flat in {walk['archetype']} walk")
    return flags


def send_telegram(text):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_CHAT_ID") or env.get("TELEGRAM_HOME_CHANNEL")
    if not token or not chat_id:
        print("[phantom] Telegram credentials not found, skipping send")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[phantom] Telegram sent: {resp.status}")
            return True
    except Exception as e:
        print(f"[phantom] Telegram failed: {e}")
        return False


def main():
    print("[phantom] Loading story map...")
    story_map = load_story_map()

    print("[phantom] Running walks...")
    walks = []
    for arch in ARCHETYPES:
        out_path = REPO_ROOT / "data" / f"walk_{arch}.json"
        # Use existing if fresh, else regenerate
        record = llm_run(arch, out_path=str(out_path))
        walks.append(record)

    print("[phantom] Scoring walks...")
    scored = []
    for walk in walks:
        scores = score_walk(walk, walks, story_map)
        scored.append({
            "archetype": walk["archetype"],
            "node_sequence": walk["path"],
            "portal_curve": walk["portal_curve"],
            "scores": scores,
            "flags": [],
        })

    kills = find_kills(walks)
    flags = find_flags(walks, story_map)

    # Attach flags to walks
    for s in scored:
        s["flags"] = [f for f in flags if s["archetype"] in f]

    report = {
        "last_run": datetime.now().isoformat(),
        "walks": scored,
        "kills_recommended": kills,
        "flags": flags,
    }

    with open(WALK_SCORES_PATH, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[phantom] Saved {WALK_SCORES_PATH}")

    # Telegram summary
    lines = ["*Phantom Walker Report*", f"Ran: {report['last_run']}"]
    for s in scored:
        lines.append(
            f"\n*{s['archetype']}*: "
            f"arc={s['scores']['dialectic_arc']} "
            f"unique={s['scores']['path_uniqueness']} "
            f"catharsis={s['scores']['cathartic_potential']}"
        )
    if kills:
        lines.append(f"\n*Kills recommended:* {', '.join(kills)}")
    if flags:
        lines.append(f"\n*Flags:* {len(flags)}")
    msg = "\n".join(lines)
    send_telegram(msg)

    print("[phantom] Done.")
    return report


if __name__ == "__main__":
    main()
