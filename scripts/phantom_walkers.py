#!/usr/bin/env python3
"""Phantom Walkers: simulate all four archetypes and score the combined experience."""
import json
import os
import re
import urllib.request
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from llm_play import run as llm_run
from headless_play import qwen_chat

REPO_ROOT = Path(__file__).parent.parent
WALK_SCORES_PATH = REPO_ROOT / "data" / "walk_scores.json"
WALK_HISTORY_PATH = REPO_ROOT / "data" / "walk_history.jsonl"
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


def min_uniqueness(paths):
    """Minimum per-walk uniqueness score (10 * (1 - Jaccard with most similar other walk))."""
    scores = []
    for i, path in enumerate(paths):
        own = set(path)
        best_sim = 0.0
        for j, other in enumerate(paths):
            if i == j:
                continue
            sim = jaccard_similarity(own, set(other))
            if sim > best_sim:
                best_sim = sim
        scores.append(round(10 * (1 - best_sim), 2))
    return min(scores) if scores else 10.0


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
    """Recommend killing generated nodes that collapse all walks into sameness.

    A node is flagged only if it appears in all 4 walks AND the downstream
    sequence from it is identical across walks AND that shared downstream is
    3+ nodes long. A terminal frontier node trivially has an identical
    (near-empty) suffix — that is convergence by design, not collapse.
    Authored nodes are never flagged; only gen_* nodes are candidates.
    """
    if len(walks) < 4:
        return []

    paths = [w["path"] for w in walks]
    # Find nodes common to all paths
    common = set(paths[0])
    for p in paths[1:]:
        common &= set(p)

    kills = []
    for node in common:
        if not node.startswith("gen_"):
            continue
        # Get downstream sequences from this node for each walk
        suffixes = []
        for p in paths:
            idx = p.index(node)
            suffixes.append(tuple(p[idx:]))

        if len(set(suffixes)) == 1 and len(suffixes[0]) >= 3:
            # All identical downstream, and the shared tail is long enough to matter
            kills.append(node)

    return kills


def score_experience(walk):
    """LLM reader-judge: rate the full playthrough against the strongest drama ever written."""
    lines = []
    choices_by_node = {c.get("node"): c for c in walk.get("choices_made", [])}
    for node_id, text in zip(walk.get("path", []), walk.get("node_texts", [])):
        lines.append(f"[{node_id}]\n{text}")
        choice = choices_by_node.get(node_id)
        if choice and choice.get("label"):
            lines.append(f"> player chose: {choice['label']}")
        elif choice and choice.get("value"):
            lines.append(f"> player wrote: {choice['value']}")
    if walk.get("act2_response"):
        lines.append(f"[ACT2 opening]\n{walk['act2_response']}")
    transcript = "\n\n".join(lines)

    prompt = (
        "You have read every great play, novel, and interactive narrative — Sophocles, "
        "Shakespeare, Chekhov, Dostoevsky, the strongest interactive fiction ever made. "
        "You are reading the transcript of one playthrough of an interactive piece in which "
        "a player converses with the Voyd, a dark dimension that feeds on wanting.\n\n"
        f"TRANSCRIPT:\n{transcript}\n\n"
        "Judge it as a reader, against that canon: Does the pressure build? Do the choices "
        "cost something? Is there a beat where you, the reader, went slack?\n\n"
        "Respond in exactly this format:\n"
        "SCORE: <0-10>\n"
        "WEAKEST: <node id of the weakest beat>\n"
        "REASON: <one or two sentences — what the weakest beat fails to do>"
    )
    raw = qwen_chat([{"role": "user", "content": prompt}], max_tokens=200, temperature=0.5)
    score_match = re.search(r"SCORE\s*:\s*(\d+)", raw, re.IGNORECASE)
    weakest_match = re.search(r"WEAKEST\s*:\s*(\S+)", raw, re.IGNORECASE)
    reason_match = re.search(r"REASON\s*:\s*(.+)", raw, re.IGNORECASE | re.DOTALL)
    return {
        "score": max(0, min(10, int(score_match.group(1)))) if score_match else None,
        "weakest": weakest_match.group(1).strip().strip("[]") if weakest_match else None,
        "reason": reason_match.group(1).strip() if reason_match else raw.strip(),
    }


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


def run_walks(act1_data=None, save=True, judge=None):
    """Run all four archetype walks and return scored walks.

    judge: run the LLM reader-judge on each transcript. Defaults to `save`
    (full nightly runs get judged; candidate-gate runs stay fast).
    """
    if judge is None:
        judge = save
    story_map = load_story_map()
    walks = []
    for arch in ARCHETYPES:
        out_path = REPO_ROOT / "data" / f"walk_{arch}.json" if save else None
        record = llm_run(arch, out_path=out_path, act1_data=act1_data)
        walks.append(record)

    scored = []
    reader_notes = []
    for walk in walks:
        scores = score_walk(walk, walks, story_map)
        entry = {
            "archetype": walk["archetype"],
            "node_sequence": walk["path"],
            "portal_curve": walk["portal_curve"],
            "scores": scores,
            "flags": [],
        }
        if judge:
            try:
                experience = score_experience(walk)
                entry["experience"] = experience
                if experience.get("weakest"):
                    reader_notes.append({
                        "archetype": walk["archetype"],
                        "score": experience.get("score"),
                        "weakest": experience["weakest"],
                        "reason": experience.get("reason", ""),
                    })
            except Exception as e:
                print(f"[phantom] reader-judge failed for {walk['archetype']}: {e}")
        scored.append(entry)

    kills = find_kills(walks)
    flags = find_flags(walks, story_map)
    for s in scored:
        s["flags"] = [f for f in flags if s["archetype"] in f]

    report = {
        "last_run": datetime.now().isoformat(),
        "walks": scored,
        "kills_recommended": kills,
        "flags": flags,
        "reader_notes": reader_notes,
    }
    return report, walks


def record_run(report):
    """Persist a walk run: overwrite walk_scores.json, append each walk to history."""
    with open(WALK_SCORES_PATH, "w") as f:
        json.dump(report, f, indent=2)
    with open(WALK_HISTORY_PATH, "a") as f:
        for walk in report["walks"]:
            f.write(json.dumps({"at": report["last_run"], **walk}) + "\n")


def walk_history_count():
    """Number of accumulated walk records (gates the immune system at 20)."""
    if not WALK_HISTORY_PATH.exists():
        return 0
    with open(WALK_HISTORY_PATH) as f:
        return sum(1 for line in f if line.strip())


def _quote(text, limit):
    flat = " ".join(text.split())
    return flat[: limit - 1] + "…" if len(flat) > limit else flat


def build_report_message(report, nodes=None, cycle_summary=None):
    """Render a walk report for a human: quote the actual beats, not just their ids."""
    if nodes is None:
        with open(REPO_ROOT / "data" / "act1_nodes.json") as f:
            nodes = json.load(f).get("nodes", {})

    when = report.get("last_run", "")[:16].replace("T", " ")
    lines = [f"🌒 Phantom Walkers — {when}",
             "Four phantom readers played the story start to finish."]
    if cycle_summary:
        lines += ["", cycle_summary]

    verdicts = []
    for s in report["walks"]:
        score = (s.get("experience") or {}).get("score")
        verdicts.append(f"{s['archetype']} {score if score is not None else '?'}/10")
    lines += ["", "How much each reader felt it:", "  " + " · ".join(verdicts)]

    by_beat = {}
    for note in report.get("reader_notes", []):
        by_beat.setdefault(note["weakest"], []).append(note)
    if by_beat:
        lines += ["", "Beats the readers stumbled on:"]
        for beat, beat_notes in sorted(by_beat.items(), key=lambda kv: -len(kv[1])):
            who = ", ".join(n["archetype"] for n in beat_notes)
            tally = f"{len(beat_notes)}/{len(report['walks'])} readers" if len(beat_notes) > 1 else who
            lines.append(f"\n▸ {beat} — flagged by {tally}")
            text = (nodes.get(beat) or {}).get("text", "")
            if text:
                lines.append(f"  “{_quote(text, 220)}”")
            for n in beat_notes:
                lines.append(f"  {n['archetype']}: {_quote(n.get('reason', ''), 300)}")

    if report.get("kills_recommended"):
        lines += ["", "⚔️ Kills recommended (all four walks collapse into the same "
                      "sequence there): " + ", ".join(report["kills_recommended"])]

    uniq = [s["scores"]["path_uniqueness"] for s in report["walks"]]
    lines += ["", f"Paths diverged {min(uniq)}–{max(uniq)}/10 across readers; "
                  f"{walk_history_count()} walks in history (immune system wakes at 20).",
              "Full playthrough transcripts: data/walk_<archetype>.json"]

    msg = "\n".join(lines)
    return msg[:4000] + "…" if len(msg) > 4000 else msg  # Telegram hard limit 4096


def test_candidate(candidate_node, act1_data):
    """Temporarily insert candidate and test path uniqueness. Returns min uniqueness score.

    The candidate is excluded from the uniqueness comparison: by construction it is
    spliced into every walk, so counting it would penalize deliberate convergence
    (choke) nodes. What matters is whether the walks still diverge around it.
    """
    import copy
    test_data = copy.deepcopy(act1_data)
    test_nodes = test_data["nodes"]

    # Find frontier nodes pointing to ACT2 and wire them to candidate
    for nid, node in test_nodes.items():
        for choice in node.get("choices", []):
            if choice.get("next") == "ACT2":
                choice["next"] = candidate_node["id"]

    # Add candidate node
    test_nodes[candidate_node["id"]] = candidate_node

    report, _ = run_walks(act1_data=test_data, save=False)
    candidate_id = candidate_node["id"]
    paths = [
        [n for n in w["node_sequence"] if n != candidate_id]
        for w in report["walks"]
    ]
    return min_uniqueness(paths), report


def main():
    print("[phantom] Loading story map...")
    report, _ = run_walks()

    record_run(report)
    print(f"[phantom] Saved {WALK_SCORES_PATH} (history: {walk_history_count()} records)")

    send_telegram(build_report_message(report))

    print("[phantom] Done.")
    return report


if __name__ == "__main__":
    main()
