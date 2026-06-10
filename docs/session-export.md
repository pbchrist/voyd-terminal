# Session Export — Voyd Terminal Evolution Pipeline

**Date:** 2026-06-09
**Branch:** feat/evolve → main
**Commits on feat/evolve this session:** 4791b34, f2a4b09, 2d961d4, c547edb, 785d196
**Final main merge:** 9b88a94

---

## What Was Built This Session

### 1. ChromaDB RAG Integration (4791b34)
- Added `query_chromadb()` and `query_rag()` to `engine/lore_index.py`
- Backend `narrative_engine.py` now queries ChromaDB first, falls back to keyword index
- Frontend `voyd_engine.js` supports `backendMode` — skips client-side `loreMap` when backend is available
- `frontend/index.html` sends leaner `/api/chat` requests (no `system_prompt`/`history` override)
- `evolve.py` queries RAG context when generating Act 2 nodes
- Added `chromadb` to `requirements.txt`

### 2. Voyd Voice Rewrite + Mythography (f2a4b09)
- Created `data/voyd_canon_mythography.md` (35KB complete canon reference)
- Added mythography to `BOOK_FILES` in `engine/lore_index.py`
- Replaced HOW YOU SPEAK block across:
  - `frontend/voyd_engine.js`
  - `engine/narrative_engine.py`
  - `data/voyd_system.md`
- New voice: storyteller mode, direct and specific, patient/seductive/wrong, short declarative sentences
- Banned words expanded: ancient, vast, eternal, whisper, shadows, abyss

### 3. Narrative Evolution Data Layer (2d961d4)
- Created `data/story_map.json` — structural map of all 31 nodes with dialectic roles, branches_to, converges_from
- Created `data/rubric.json` — 3-axis scoring rubric (dialectic_function, tension_advancement, branch_choke_logic) with auto-promote (≥24) and auto-kill (<18) thresholds
- Created `data/canon_events.json` — 10 unused canon moments from Books 1 & 2, each with Voyd POV, tension level, source
- Added Narrative Evolution Directives section to `AGENTS.md`

### 4. Evolution Pipeline Implementation (c547edb — authored by previous Kimi session, then audited)
- Rewired `gen_1` through `gen_12` in `data/act1_nodes.json` into converging-diamond pattern
- `gen_13` generated from `portal_moves_overnight` canon event
- `frontend/index.html` updated to traverse `next` pointers that are real node IDs (not just `ACT2`)
- `start.sh` now prefers `.venv/bin/python` if available
- Created `tests/test_evolution_directives.py`

### 5. Audit Fixes (785d196)
- `generate_node()` now calls local Qwen API (`localhost:8081/v1/chat/completions`) with structured prompt using canon event `voyd_pov` as seed
- Fallback to template generation if API unavailable
- `score_node()` tension_advancement replaced hardcoded `portal_moves_overnight` word list with event-agnostic `INTENSE_WORDS` and `DYNAMIC_WORDS` sets
- `detect_structural_issues()` expanded to detect branches open too long with no choke, and acts with no tension increase
- Structural issues sent to Telegram before exiting
- Uncertain zone (18-23): polls `getUpdates` for up to 24 hours for Patrick's YES/NO/NOT YET reply
- `recalibrate_rubric()` actually analyzes last 10 decisions, computes drift from thresholds, adjusts weights (applied immediately)
- Added `scripts/hunt_itch.py` for weekly itch.io Twine structural analysis
- Added weekly cron note to `AGENTS.md`
- Added regression tests for event-agnostic scoring and real recalibration

---

## Current Architecture State

| Layer | Status |
|-------|--------|
| Act 1 graph (authored) | 19 nodes, 4 archetype paths, fully wired |
| Act 2 generated nodes | gen_1 through gen_13, converging-diamond pattern |
| RAG | ChromaDB at `/home/patrick/voyd_graph_rag/chromadb` with 985 passages |
| LLM | Local Qwen3.6-27B-Q6_K at `http://localhost:8081/v1` |
| Backend | FastAPI on port 8765, venv Python, CORS open |
| Frontend | Vanilla JS, GitHub Pages, loads `voyd_data.json` |
| Voice | Storyteller mode, lowercase, direct/specific, no evasion |
| Evolution | Daily cron at 03:00, weekly itch hunt Sundays at 04:00 |

---

## Key Decisions Made

1. **Do not implement planned infrastructure yet.** Immune System, Phantom Walkers, and Gravity Wells are fully specified in `AGENTS.md` under `## Planned Infrastructure` but must wait until `data/walk_scores.json` has ≥20 records (5 evolution cycles).

2. **Auto-promote threshold stays at 24/30.** This was validated by the test suite; the `portal_moves_overnight` event scores 28/30 with the new event-agnostic rubric.

3. **Rubric weight recalibration is applied immediately, not just suggested.** The `pending_weight_suggestion` field is written but weights are also updated in `rubric["axes"][axis]["weight"]`.

4. **Telegram uncertain zone defaults to "hold" on timeout.** If Patrick does not reply within 24 hours, the event remains unused and the script exits with code 3.

5. **Generated nodes are always `type: "beat"` for now.** The `generate_node()` function does not yet produce `branch` or `choke` nodes. The Immune System spec addresses this gap.

---

## Files a Future Kimi Session Should Read First

1. `AGENTS.md` — project architecture, testing protocol, evolution directives, planned infrastructure
2. `data/voyd_canon_mythography.md` — complete worldbuilding reference
3. `data/story_map.json` — current structural state
4. `data/rubric.json` — current scoring weights and decision history
5. `data/canon_events.json` — unused dramatically charged moments
6. `evolve.py` — evolution pipeline implementation
7. `frontend/voyd_engine.js` — client-side narrative engine
8. `engine/narrative_engine.py` — backend narrative engine

---

## Testing Protocol (from AGENTS.md)

Before every commit/push:
1. `./start.sh` starts without errors
2. `curl http://localhost:8765/api/health` returns 200
3. Graph integrity: all paths from `1.0` → `10.0` resolve
4. Act 1 traversal: all 4 archetypes set `portalValue`, `archetype`, `playerAnswer` correctly
5. Act 2 handoff: session state reaches `buildSystemPrompt` in `voyd_engine.js`
6. `python3 -m unittest tests.test_evolution_directives -v` passes

---

## Open Questions / Known Gaps

- The frontend `voyd_engine.js` still builds system prompts client-side even in backend mode (though `backendMode` skips lore chunks). The backend rebuilds its own prompt. This is harmless redundancy.
- No session persistence across server restarts (in-memory dict).
- CORS is `allow_origins=["*"]`.
- The itch.io scraper (`scripts/hunt_itch.py`) may break if itch.io changes their HTML structure.
- `detect_structural_issues()` checks gen_1–gen_19, but the upper bound is arbitrary. Should scale dynamically.

---

## How to Resume Work

If starting a new session:
```bash
cd /home/patrick/voyd-terminal
git checkout main
git pull origin main
python3 -m unittest tests.test_evolution_directives -v
```

If implementing Planned Infrastructure systems, read `AGENTS.md` section `## Planned Infrastructure` first. Do not build until walk data exists.
