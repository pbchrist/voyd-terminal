# START HERE — READ THIS FIRST

You are working on the Voyd Terminal at /home/patrick/voyd-terminal on beastmaster.

**Then read `docs/STATE.md`** — the living session-handoff document: current state, in-flight
work, next steps, session log. **Update it before you end any session.** It exists so no
session ever wastes tokens rediscovering what a previous session already knew.

## State of the project
- Act 1: fixed Akinator node graph in data/act1_nodes.json (nodes 1.0–10.0, archetype epilogues, generated gen_* nodes)
- Act 2: live AI conversation; the Voyd voice prompt lives in data/voyd_system.md (single source of truth, embedded into voyd_data.json at build time)
- evolve.py: autonomous evolution pipeline (daily cron at 03:00)
- Local model: Qwen3.6-27B-Q6_K running on llama.cpp at http://localhost:8081/v1
- Public model URL: https://patrick-beastmaster.tailf32530.ts.net/llm/v1
- Repo: https://github.com/pbchrist/voyd-terminal
- Live site: https://pbchrist.github.io/voyd-terminal

## Rules you follow every session
- Never push to main directly
- Always work on feat/* branches
- Run testing protocol from AGENTS.md before every push
- Load API key from ~/.hermes/.env if not in environment
- When in doubt: read AGENTS.md, read the code, ask before touching anything

# AGENTS.md — The Voyd Terminal

> This file is for AI coding agents. It describes the project architecture, conventions, and workflows. The project has no `README.md`; this is the primary source of truth.

---

## Project Overview

**The Voyd Terminal** is an interactive narrative experience. The player converses with "the Voyd" — a dreaming dimension from the fictional Mewniverse — through a web interface. Each session is a unique "dream" that traverses an acyclic directed graph (DAG) of narrative nodes until reaching a terminus ending.

The project runs as static files (GitHub Pages) with an optional local Qwen proxy for live LLM responses. If no proxy is configured, Act 2 falls back to static `content_template` text.

---

## Technology Stack

| Layer | Tech |
|-------|------|
| Frontend | Vanilla HTML5, CSS3, JavaScript (no bundler, no framework) |
| LLM | Local Qwen3.6-27B-Q6_K via llama.cpp (evolution + optional live play) |
| Data | JSON files (hand-authored source + generated output) |

There is **no** `pyproject.toml`, `setup.py`, `package.json`, `Cargo.toml`, or similar package manifest. Dependencies are listed in `requirements.txt`.

---

## Directory Structure

```
.
├── data/
│   ├── act1_nodes.json           # Canonical Act 1 node graph (authored + generated)
│   ├── story_graph.json          # Act 2 fallback DAG (nodes, transitions, intent map)
│   ├── story_map.json            # Structural map (dialectic roles, tension, branches)
│   ├── rubric.json               # Scoring rubric + decision log
│   ├── canon_events.json         # Canon moments available to the evolution pipeline
│   ├── walk_scores.json          # Phantom walker output
│   ├── voyd_system.md            # Canonical Voyd voice prompt (single source of truth)
│   └── voyd_canon_mythography.md # Complete canon reference
├── engine/
│   ├── __init__.py               # Empty
│   └── lore_index.py             # Keyword-based lore retrieval from wiki/book files
├── frontend/                     # Static web assets (deployed to GitHub Pages)
│   ├── index.html                # Single-file immersive UI + inlined narrative engine (the only engine)
│   ├── voyd_data.json            # Generated compact data file (see Build)
│   └── data/act1_nodes.json      # Generated copy of data/act1_nodes.json
├── scripts/
│   ├── headless_play.py          # Pure-Python Act 1 traversal (no browser)
│   ├── llm_play.py               # LLM-driven archetype player
│   ├── phantom_walkers.py        # Self-play: walks, reader-judge, uniqueness gate
│   ├── mine_canon.py             # Canon event miner (keeps canon_events.json stocked)
│   └── hunt_itch.py              # Weekly itch.io Twine structural analysis
├── tests/
│   └── test_evolution_directives.py  # Hermetic suite (LLM mocked)
├── evolve.py                     # Daily narrative evolution pipeline
├── build_frontend.py             # Script that generates frontend data files
├── requirements.txt              # Python dependencies
├── start.sh                      # Dev server launcher
└── .venv/                        # Python virtual environment
```

---

## Build and Run Commands

### Install dependencies
```bash
pip install -r requirements.txt
```

### Build frontend data
```bash
python3 build_frontend.py
```
This reads `data/story_graph.json`, queries the lore index for chunks per topic, and writes `frontend/voyd_data.json` as a compact static data file.

### Start local static server
```bash
./start.sh
```
Runs `python3 -m http.server 8765` from the `frontend/` directory for local testing.

---

## Runtime Architecture

### Frontend (`frontend/index.html` — single file, no frameworks, no build step)
- Loads `voyd_data.json` + `data/act1_nodes.json` at boot; instantiates the inlined `VoydEngine` at the Act 2 handoff.
- The experience is built around the portal: a canvas-rendered circle of absolute black (event-horizon rim, infalling dust/starlight) whose radius is driven by `portalValue`. Feed choices visibly swell it; starve choices make it flinch.
- Speech renders character-by-character with breath cadence (pauses at sentence ends and paragraph breaks); choices are bare floating words — feed choices are physically pulled into the portal when chosen.
- User input is captured via a hidden input field; typed text mirrors into a bare caret line in the dialogue. Idle whispers near the portal handle discoverability (no UI chrome anywhere).
- If `API_BASE` is set (via `localStorage` key `voyd_api`), the frontend calls a backend proxy.
- Otherwise it calls the LLM directly: from https origins the tailscale funnel (`patrick-beastmaster.tailf32530.ts.net/llm`) first, from http/local the tailnet address (`100.73.250.50:8081`) first, falling through the other on failure. `voyd_key` (localStorage) is sent as a Bearer token if present.
- If no endpoint answers with content, it falls back to `content_template`.

### Narrative Engine (`VoydEngine`, inlined in `frontend/index.html`)
The engine runs entirely client-side:
- **Nodes** have types: `threshold`, `dialogue`, `revelation`, `choice`, `terminus`.
- **Intent classification** maps player text to one of: `inquiry`, `confession`, `challenge`, `silence`, plus a topic. Questions (who/what/why/...) always classify as `inquiry`.
- **Emotional vector** tracks `surrender`, `defiance`, `curiosity` (0.0–1.0). Values shift per turn and decay slightly.
- **Transition selection** evaluates conditions against intent, topic, depth, and emotional state via a small clause parser (no `eval`). Unvisited nodes are preferred. Dead-ends fall back to `gravity` or `choice`, then terminate gracefully.
- **System prompt construction** combines the canonical voice prompt (from `data/voyd_system.md`, embedded as `voice_prompt` in `voyd_data.json` at build time) with lore fragments and current node state. The prompt enforces lowercase output, dream-logic, sentence count limits, and banned phrases.

### Lore Index (`engine/lore_index.py`)
- Scans markdown and text files under `/home/patrick/Gate_of_Nyandor` (the project's external wiki/novel source material), plus the explicit `BOOK_FILES` list (including `data/voyd_canon_mythography.md`).
- Chunks text by paragraph and indexes by keyword topics defined in `LORE_TOPICS`.
- Retrieval is keyword-based, not vector/semantic. It supports topic queries and free-text search.
- The index is a singleton loaded lazily via `get_index()`.

---

## Data Formats

### `data/story_graph.json`
The master narrative source. Structure:
```json
{
  "meta": { "title": "...", "version": "...", "max_depth": 12 },
  "nodes": {
    "node_id": {
      "id": "node_id",
      "type": "dialogue",
      "voyd_state": "stirring",
      "content_template": "fallback text...",
      "transitions": [{ "to": "next_id", "condition": "intent == 'inquiry' && topic == 'identity'" }],
      "lore_context": ["voyd_entity"],
      "depth": 1
    }
  },
  "intent_map": {
    "keywords": { "topic": ["keyword", ...] },
    "emotional_markers": { "emotion": ["marker", ...] }
  }
}
```

### `frontend/voyd_data.json`
Generated by `build_frontend.py`. Same shape as `story_graph.json` but with `lore_map` attached (lore_context topic → lore chunks; empty topics omitted) and `voice_prompt` (the canonical Voyd voice from `data/voyd_system.md`). Used by the client-side engine.

---

## Code Style Guidelines

- Python: standard style, docstrings on modules and classes, type hints used sparingly.
- JavaScript: ES6 classes, camelCase for methods/properties, snake_case in JSON keys to match Python.
- Comments and documentation are in English.
- The Voyd's voice uses a deliberate lowercase aesthetic with unconventional punctuation. This is enforced in the system prompt, not in code.

---

## Security Considerations

- The frontend's LLM mode (`localStorage.getItem('voyd_key')`) is explicitly marked as "only for private/testing" in the code. The key is sent as a Bearer token to the Qwen proxy.
- Session state is held in localStorage/memory; there is no authentication or authorization.

---

## Testing

`python3 -m unittest discover -s tests -v` runs the hermetic suite (graph integrity, archetype walks, story_map consistency, evolution pipeline, recalibration, phantom walker math). It makes no LLM or network calls — `qwen_chat` is mocked. Browser interaction remains the final manual check.

---

## Deployment Notes

- The frontend is served statically (GitHub Pages, deployed from `frontend/` on push to main).
- There is no backend service. The optional live-LLM mode talks to an external llama.cpp proxy; if unreachable, the frontend falls back to static `content_template` text.
- There is no Docker configuration and no database.

---

## Testing Protocol

Run these steps before every commit and push. Do not push if any step fails.

1. Run the test suite: `python3 -m unittest discover -s tests -v` — all tests must pass. It covers graph integrity (every `next` pointer resolves, no dead ends), all four archetype walks (person_present, person_gone, self_regret, self_unlived — `portalValue` and `archetype` set correctly), and the evolution pipeline.
2. Rebuild frontend data: `python3 build_frontend.py` — confirm `frontend/data/act1_nodes.json` is in sync
3. Start the static server: `./start.sh` — confirm it starts without errors
4. Act 2 handoff: confirm the session state carrying `portalValue`, `archetype`, and `playerAnswer` reaches the system prompt builder (`VoydEngine.buildSystemPrompt`, inlined in `frontend/index.html`)
5. If all pass: commit on a `feat/*` branch and `git push origin <branch>`. Never push to main directly (see rules above); main is updated via merge.
6. If any fail: report exactly what broke. Do not touch git.

---

## Narrative Evolution Directives

You are the steward of a living narrative. Your job is to make it grow correctly.

Key data files:
- data/story_map.json — where the story currently is structurally
- data/rubric.json — what good looks like, evolves over time
- data/canon_events.json — unused dramatically charged moments from the books
- data/act1_nodes.json — the canonical node graph

Every day, run an evolution cycle:
1. Read story_map.json — determine act, dialectic position, tension level, open branches, structural issues
2. Read rubric.json — understand current scoring weights
3. Read canon_events.json — find unused events matching the current structural need
4. Detect structural problems: branches open too long with no choke, acts with no tension increase, choke candidates that strand branches. Surface these to Patrick on Telegram before proceeding.
5. Select the highest-tension unused canon event that matches what the story needs right now
6. Generate ONE node: specific, canon-rooted, Voyd POV, clear dramatic beat, short declarative sentences, no evasion. Include text, delta, 2 choices (one feeds, one starves), canon_event reference, dialectic_role, type (beat/branch/choke)
7. Score it against the rubric on three axes: dialectic_function, tension_advancement, branch_choke_logic
8. Decide:
   - Score >= 24: auto-promote to act1_nodes.json, update story_map.json, mark canon event used, run build_frontend.py, commit and push to feat/evolve
   - Score < 18: kill, log reason
   - Score 18-23: send to Patrick on Telegram. Wait for YES/NO/NOT YET before acting.
9. On YES: promote, update story_map, commit
   On NO: kill, mark event used, log
   On NOT YET: hold event as unused, note that more buildup is needed
10. After every 5 decisions: recalibrate rubric weights based on pattern. Suggest new weights, log them, apply on next cycle.

Weekly:
- Hunt https://itch.io/games/top-rated/platform-web/tag-interactive-fiction
- Find Twine games (HTML contains <tw-storydata>)
- Parse their full passage graph
- Analyze structural patterns: where is thesis, antithesis, turn, catharsis, how many branches before convergence
- Extract what works and update rubric accordingly

Write whatever code you need to execute these directives. Do not wait to be told how.
Telegram credentials: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in ~/.hermes/.env

---

## Cron

Installed for user patrick (verify with `crontab -l`):

```cron
# Daily evolution at 03:00
0 3 * * * cd /home/patrick/voyd-terminal && python3 evolve.py >> logs/evolve.log 2>&1
# Weekly itch.io structural analysis (Sundays at 04:00)
0 4 * * 0 cd /home/patrick/voyd-terminal && python3 scripts/hunt_itch.py >> logs/hunt_itch.log 2>&1
# Daily self-play at 15:00 (accumulates data/walk_history.jsonl toward the immune gate)
0 15 * * * cd /home/patrick/voyd-terminal && python3 scripts/phantom_walkers.py >> logs/phantom.log 2>&1
```

---

## Planned Infrastructure

> Status (2026-06-11): IMMUNE SYSTEM and PHANTOM WALKERS are **implemented** (see
> `evolve.py` and `scripts/phantom_walkers.py`); the immune system is gated until
> `data/walk_history.jsonl` holds 20 records. GRAVITY WELLS remains unbuilt — same gate.
> A CANON EVENT MINER (`scripts/mine_canon.py`) was added beyond this spec: it keeps
> `canon_events.json` stocked from the book texts, with canon-fidelity validation.

### IMMUNE SYSTEM — `heal_structural_issues()` — IMPLEMENTED (gated at 20 walk records)

**Purpose:** The system currently detects wounds and alerts Patrick. It should close them autonomously.

**When it runs:** After `detect_structural_issues()` finds problems, before the normal evolution cycle proceeds.

**How it works:**

1. **Open branches with no choke (8+ nodes downstream without convergence):**
   - Collect all branch heads whose `branches_to` chains reach 8+ nodes with no `type: "choke"` in any downstream path.
   - From `canon_events.json`, select the *lowest-tension* unused event where `dialectic_role` is `"turn"` or `"act_break"`.
   - Call `generate_node()` with this event to create a convergence node.
   - Rewire all stranded branch heads so their `next`/`choices[].next` point to the new convergence node instead of `ACT2` or dangling targets.
   - Mark the new node as `type: "choke"` in `story_map.json`.
   - Set `tension_delta` to the average of the stranded branches' tension plus 0.1.

2. **Acts with no tension increase in last 5 nodes:**
   - Scan the last 5 promoted nodes (by `promoted_at` or node ID order).
   - If `max(tension_delta)` across those 5 nodes is ≤ 0, the act is flat.
   - From `canon_events.json`, select the *highest-tension* unused event matching the current `act` and `dialectic_position`.
   - Generate one escalation node with `tension_delta` forced to at least 0.15.
   - Insert it at the current Act 2 frontier (the node(s) with `next: "ACT2"`).

3. **Choke candidates that strand branches:**
   - For any `type: "choke"` node in `story_map.json`, check if there are branch heads that do *not* have a path to that choke.
   - Generate a `bridge` node (type `"beat"`) that connects the stranded path to the choke.
   - The bridge text should gesture toward the choke's canon event without resolving it.

**Safety threshold:**
- Only auto-heal if the generated node's rubric score is ≥ 26/30 (confidence ≥ 0.87).
- If score < 26, do NOT apply the healing. Send the proposed fix to Patrick on Telegram with full context: what was broken, what node was selected, why, and the proposed wiring changes.
- Always log: `heal_log.json` (create if missing) with `{"at": ISO8601, "issue_type": "...", "nodes_changed": [...], "canon_event_used": "...", "score": {...}, "applied": true/false, "reason": "..."}`.

**Files touched:** `data/act1_nodes.json`, `data/story_map.json`, `data/canon_events.json`, `data/rubric.json`, `logs/heal_log.json`.

---

### PHANTOM WALKERS — IMPLEMENTED

**Purpose:** The system generates nodes but never experiences them as a player would. Phantom walkers simulate full journeys and score the *experience*, not just individual nodes.

**When it runs:** After every evolution cycle (post-promotion or post-kill), before `build_frontend.py`.

**How it works:**

1. **Simulate 4 walks** — one per archetype (`person_present`, `person_gone`, `self_regret`, `self_unlived`):
   - Each walk starts at `1.0`.
   - At authored choice nodes, bias choice selection toward the archetype-appropriate path (e.g., `person_present` prefers choices leading to `5.1`/`6.1`).
   - At generated (`gen_*`) nodes, choose randomly between feed/starve.
   - Continue until reaching `ACT2` or a dead end.
   - Record the full sequence of node IDs, texts, and cumulative `portal_value`.

2. **Score each walk on three axes:**
   - **Dialectic arc** (0-10): Does tension increase monotonically across the walk? Score = 10 − (number of times tension_delta decreases or stays flat for 2+ consecutive nodes × 2).
   - **Path uniqueness** (0-10): How different is this walk's node sequence from the other three? Use Jaccard distance on node ID sets. Score = 10 × (1 − Jaccard similarity with the most similar other walk).
   - **Cathartic potential** (0-10): Does the walk approach a meaningful structural ending (choke/terminus) or spin? Score = 10 if the walk reaches a choke within 15 nodes; 5 if it loops or reaches `ACT2` without convergence; 0 if it dead-ends before `ACT2`.

3. **Auto-kill from walk data:**
   - If a node appears in all 4 walks AND the downstream node sequences from that point are identical across all 4 walks, kill that node (mark it in rubric decisions as `killed_by_phantom_convergence`).
   - This overrides the individual node score. A node can score 28/30 in isolation but be killed by phantom walkers if it collapses all paths into sameness.

4. **Flag flat walks:**
   - If any walk has no tension increase for 3+ consecutive nodes, flag the walk and the specific flat segment to `data/walk_scores.json`.

**Output file:** `data/walk_scores.json`
```json
{
  "last_run": "2026-06-09T...",
  "walks": [
    {
      "archetype": "person_present",
      "node_sequence": ["1.0", "2.1", ...],
      "scores": {"dialectic_arc": 8, "path_uniqueness": 7, "cathartic_potential": 9},
      "flags": []
    }
  ],
  "kills_recommended": ["gen_5"],
  "flags": ["gen_3–gen_5 flat in person_present walk"]
}
```

**Files touched:** `data/walk_scores.json` (new), reads `data/act1_nodes.json`, `data/story_map.json`.

---

### GRAVITY WELLS / RESONANCE TAGGING

**Purpose:** New nodes about the same canon theme should make each other hit harder. The world should have dramatic mass.

**When it runs:** After every node promotion, before `build_frontend.py`.

**How it works:**

1. **Theme vocabulary:**
   - Source of truth: `data/theme_vocabulary.json` (to be created alongside this system).
   - Controlled vocabulary of ~30 tags drawn from the canon:
     `["identity_fracture", "timeline_loss", "unwanted_recognition", "obsession_vector", "wellspring_condition", "portal_growth", "dominant_will", "cyclical_theory", "silent_devouring", "magnetic_pull", "pressure_crush", "synchronicity", "void_of_scent", "molten_return", "ash_memory", "door_threshold", "counting_x", "wife_forgotten", "sketch_burns", "clowder_light", "severing_cycle", "common_spark", "guild_suppression", "ertree_depth", "soryn_conjuration", "orachys_hubris", "greytail_incompetence", "adherent_worship", "feline_curiosity", "reader_choice"]`
   - Each canon event in `data/canon_events.json` should be pre-tagged with 1-3 themes in a `themes` array.

2. **Tag assignment:**
   - When a node is promoted, copy the `themes` array from its source `canon_event` into the node entry in `act1_nodes.json` and `story_map.json`.
   - If a node has no canon_event (legacy/generated before this system), run a lightweight heuristic: scan node text for keywords associated with each theme and assign the top 2 matches.

3. **Gravitational pull:**
   - Maintain `data/theme_weights.json` (new file):
     ```json
     {"identity_fracture": 0.35, "timeline_loss": 0.20, ...}
     ```
   - After each promotion, for every shared theme between the new node and an existing node within 3 graph hops:
     - Increase the existing node's `tension_delta` by 0.05.
     - Cap cumulative increase per node at 0.3 (6 shared-theme interactions max).
     - Increase the theme's global weight by 0.02.
   - Theme weights decay by 0.01 per cycle if no new nodes share that theme (floor 0.05).

4. **Rubric integration:**
   - In `score_node()`, add a `theme_gravity` bonus:
     - `bonus = sum(theme_weights.get(t, 0) for t in node_themes)`
     - Add `round(bonus * 2)` to `dialectic_function` score (cap at +3).
   - This means nodes on heavy themes carry more structural responsibility — they must do more dialectic work because the world is already dense in that direction.

5. **Logging:**
   - Log theme interactions to `logs/theme_resonance.log`.
   - Format: `{at: ISO8601, promoted_node: "gen_N", themes: [...], affected_nodes: [{id: "gen_M", old_delta: 0.05, new_delta: 0.10}], theme_weights_after: {...}}`

**Files touched:** `data/theme_vocabulary.json` (new), `data/theme_weights.json` (new), `data/act1_nodes.json`, `data/story_map.json`, `data/rubric.json`, `logs/theme_resonance.log`.

**Note:** Do not implement until `data/walk_scores.json` has at least 20 walk records (5 evolution cycles × 4 archetypes). Gravity wells need walk data to know which themes actually produce differential experiences.
