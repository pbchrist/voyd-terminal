#!/usr/bin/env python3
"""Canon event miner: keeps the evolution pipeline fed.

Walks through the book texts with a rotating cursor (data/mine_state.json),
asks the local Qwen to extract dramatically charged Voyd moments, validates
each candidate against canon (the mythography's prohibited distortions) and
for dramatic charge, dedupes against existing events, and appends accepted
candidates to data/canon_events.json with used=false.

CLI: python3 scripts/mine_canon.py [--max 5]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from headless_play import qwen_chat

REPO_ROOT = Path(__file__).resolve().parents[1]
CANON_EVENTS_PATH = REPO_ROOT / "data" / "canon_events.json"
MINE_STATE_PATH = REPO_ROOT / "data" / "mine_state.json"
MYTHOGRAPHY_PATH = REPO_ROOT / "data" / "voyd_canon_mythography.md"

BOOK_SOURCES = [
    ("Book 1", Path("/home/patrick/Gate_of_Nyandor/book1_text.txt")),
    ("Book 2", Path("/home/patrick/Gate_of_Nyandor/book2_text.txt")),
]

SEGMENT_CHARS = 6000
SEGMENT_OVERLAP = 400
ACCEPT_THRESHOLD = 7
DUPLICATE_JACCARD = 0.5

DIALECTIC_ROLES = {
    "establishing_antithesis", "antithesis_deepening", "antithesis_peak",
    "turn", "synthesis_attempt", "catharsis", "act_break",
}


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat()}] [miner] {msg}"
    print(line)
    log_path = REPO_ROOT / "logs" / "evolve.log"
    log_path.parent.mkdir(exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def parse_json_reply(raw: str):
    raw = raw.strip()
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0].strip()
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0].strip()
    return json.loads(raw)


def fidelity_context() -> str:
    """Canon guardrails for the validator: the prohibited-distortions addendum."""
    try:
        text = MYTHOGRAPHY_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""
    match = re.search(r"## ADDENDUM F.*?(?=\n## |\Z)", text, re.DOTALL)
    return match.group(0).strip() if match else text[:2000]


def load_mine_state() -> dict:
    if MINE_STATE_PATH.exists():
        return json.loads(MINE_STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_mine_state(state: dict) -> None:
    MINE_STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def next_segment(state: dict, label: str, path: Path) -> str | None:
    """Return the next segment of a book, advancing the rotating cursor."""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    if not text:
        return None
    cursor = state.get(label, 0) % len(text)
    segment = text[cursor:cursor + SEGMENT_CHARS]
    if len(segment) < SEGMENT_CHARS:
        segment += text[:SEGMENT_CHARS - len(segment)]  # wrap around
    state[label] = (cursor + SEGMENT_CHARS - SEGMENT_OVERLAP) % len(text)
    return segment


def word_set(text: str) -> set:
    return set(re.findall(r"[a-z']+", text.lower()))


def is_duplicate(candidate: dict, existing: list[dict]) -> bool:
    cand_words = word_set(candidate.get("event", ""))
    if not cand_words:
        return True
    for event in existing:
        if event.get("id") == candidate.get("id"):
            return True
        known = word_set(event.get("event", ""))
        union = cand_words | known
        if union and len(cand_words & known) / len(union) > DUPLICATE_JACCARD:
            return True
    return False


def slugify(text: str, existing_ids: set) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "mined_event"
    base, n = slug, 2
    while slug in existing_ids:
        slug = f"{base}_{n}"
        n += 1
    return slug


def normalize_candidate(raw: dict, source: str, existing_ids: set) -> dict | None:
    event = str(raw.get("event", "")).strip()
    voyd_pov = str(raw.get("voyd_pov", "")).strip().lower().replace("—", " ")
    if len(event) < 30 or len(voyd_pov) < 15:
        return None
    role = str(raw.get("dialectic_role", "")).strip()
    if role not in DIALECTIC_ROLES:
        role = "antithesis_deepening"
    try:
        tension = max(0.0, min(1.0, float(raw.get("tension_level", 0.5))))
    except (TypeError, ValueError):
        tension = 0.5
    try:
        act = int(raw.get("act", 2))
    except (TypeError, ValueError):
        act = 2
    act = act if act in (2, 3) else 2
    return {
        "id": slugify(str(raw.get("id", "")) or event, existing_ids),
        "act": act,
        "dialectic_role": role,
        "event": event,
        "voyd_pov": voyd_pov,
        "tension_level": round(tension, 2),
        "source": f"{source} (mined)",
        "used": False,
        "mined": True,
        "mined_at": datetime.now().isoformat(),
    }


def extract_candidates(segment: str, source: str) -> list[dict]:
    prompt = (
        "You are reading a segment of the Gate of Nyandor books, hunting for canon events "
        "for an interactive narrative spoken by the Voyd (the dark dimension beneath the Mewniverse).\n\n"
        f"SEGMENT ({source}):\n{segment}\n\n"
        "Find 0-2 dramatically charged moments in this segment that involve the Voyd, the portal, "
        "obsession, the Severing, timelines, or the cost of wanting. Skip mundane scenes — only "
        "moments with real dramatic mass. If nothing qualifies, return [].\n\n"
        "For each moment return:\n"
        '- "id": short snake_case identifier\n'
        '- "event": 2-3 factual sentences describing what happens\n'
        '- "voyd_pov": 1-3 sentences, first person AS the Voyd, entirely lowercase, '
        "short declarative sentences, no em dashes, patient and slightly wrong\n"
        '- "act": 2 or 3\n'
        '- "dialectic_role": one of establishing_antithesis, antithesis_deepening, '
        "antithesis_peak, turn, synthesis_attempt, catharsis, act_break\n"
        '- "tension_level": 0.0-1.0\n\n'
        "Return ONLY a JSON array."
    )
    raw = qwen_chat([{"role": "user", "content": prompt}], max_tokens=600, temperature=0.7)
    parsed = parse_json_reply(raw)
    return parsed if isinstance(parsed, list) else []


def validate_candidate(candidate: dict, guardrails: str) -> tuple[int, str]:
    """Grade canon fidelity + dramatic charge 0-10. Accept at ACCEPT_THRESHOLD."""
    prompt = (
        "You are the canon keeper for the Gate of Nyandor series. "
        "Judge this proposed canon event on two things at once: "
        "(1) fidelity — does it violate any of the canon rules below? "
        "(2) dramatic charge — judged against the strongest dramatic beats in literature, "
        "is this a moment with real stakes, cost, and irreversibility?\n\n"
        f"CANON RULES (violations are fatal):\n{guardrails}\n\n"
        f"PROPOSED EVENT:\n{json.dumps(candidate, indent=2)}\n\n"
        "A canon violation caps the score at 3. Mundane or repetitive moments score below 7.\n"
        "Respond in exactly this format:\n"
        "SCORE: <0-10>\n"
        "REASON: <one sentence>"
    )
    raw = qwen_chat([{"role": "user", "content": prompt}], max_tokens=150, temperature=0.3)
    match = re.search(r"SCORE\s*:\s*(\d+)", raw, re.IGNORECASE)
    score = max(0, min(10, int(match.group(1)))) if match else 0
    reason_match = re.search(r"REASON\s*:\s*(.+)", raw, re.IGNORECASE | re.DOTALL)
    reason = reason_match.group(1).strip() if reason_match else raw.strip()
    return score, reason


def mine(max_accept: int = 5, max_segments: int = 12, root: Path = REPO_ROOT) -> list[dict]:
    """Mine up to max_accept new canon events. Appends to canon_events.json."""
    events_path = root / "data" / "canon_events.json"
    existing = json.loads(events_path.read_text(encoding="utf-8"))
    existing_ids = {e.get("id") for e in existing}
    guardrails = fidelity_context()
    state = load_mine_state()
    accepted: list[dict] = []
    segments_done = 0

    while len(accepted) < max_accept and segments_done < max_segments:
        for label, path in BOOK_SOURCES:
            if len(accepted) >= max_accept or segments_done >= max_segments:
                break
            segment = next_segment(state, label, path)
            segments_done += 1
            if not segment:
                continue
            try:
                candidates = extract_candidates(segment, label)
            except Exception as exc:
                log(f"extraction failed on {label} segment: {exc}")
                continue
            for raw_cand in candidates:
                if len(accepted) >= max_accept:
                    break
                cand = normalize_candidate(raw_cand, label, existing_ids)
                if cand is None:
                    continue
                if is_duplicate(cand, existing + accepted):
                    log(f"duplicate skipped: {cand['id']}")
                    continue
                try:
                    score, reason = validate_candidate(cand, guardrails)
                except Exception as exc:
                    log(f"validation failed for {cand['id']}: {exc}")
                    continue
                if score >= ACCEPT_THRESHOLD:
                    cand["mine_score"] = score
                    accepted.append(cand)
                    existing_ids.add(cand["id"])
                    log(f"accepted {cand['id']} (score {score}): {reason[:80]}")
                else:
                    log(f"rejected {cand['id']} (score {score}): {reason[:80]}")

    if accepted:
        existing.extend(accepted)
        events_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    save_mine_state(state)
    log(f"mining complete: {len(accepted)} accepted from {segments_done} segments")
    return accepted


def main() -> int:
    parser = argparse.ArgumentParser(description="Mine canon events from the books")
    parser.add_argument("--max", type=int, default=5, help="max events to accept")
    parser.add_argument("--segments", type=int, default=12, help="max segments to scan")
    args = parser.parse_args()
    accepted = mine(max_accept=args.max, max_segments=args.segments)
    for event in accepted:
        print(f"  + {event['id']} (tension {event['tension_level']}, {event['dialectic_role']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
