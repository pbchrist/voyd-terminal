# AGENTS.md — The Voyd Terminal

> This file is for AI coding agents. It describes the project architecture, conventions, and workflows. The project has no `README.md`; this is the primary source of truth.

---

## Project Overview

**The Voyd Terminal** is an interactive narrative experience. The player converses with "the Voyd" — a dreaming dimension from the fictional Mewniverse — through a web interface. Each session is a unique "dream" that traverses an acyclic directed graph (DAG) of narrative nodes until reaching a terminus ending.

The project has two runtime modes:

1. **Backend mode** (recommended): A FastAPI server securely proxies calls to the Anthropic Claude API.
2. **Standalone mode** (testing only): The frontend runs as static files and calls Anthropic directly from the browser with an exposed API key.

---

## Technology Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3, FastAPI, Uvicorn, Pydantic, httpx |
| Frontend | Vanilla HTML5, CSS3, JavaScript (no bundler, no framework) |
| LLM | Anthropic Claude (`claude-sonnet-4-20250514`) |
| Data | JSON files (hand-authored source + generated output) |

There is **no** `pyproject.toml`, `setup.py`, `package.json`, `Cargo.toml`, or similar package manifest. Dependencies are listed in `requirements.txt`.

---

## Directory Structure

```
.
├── data/
│   └── story_graph.json          # Master narrative DAG (nodes, transitions, intent map)
├── engine/                       # Python backend package
│   ├── __init__.py               # Empty
│   ├── main.py                   # FastAPI app and HTTP endpoints
│   ├── narrative_engine.py       # DAG traversal, intent classification, prompt builder
│   └── lore_index.py             # Keyword-based lore retrieval from external wiki files
├── frontend/                     # Static web assets
│   ├── index.html                # Single-page immersive UI
│   ├── voyd_engine.js            # Client-side narrative engine (mirrors Python logic)
│   └── voyd_data.json            # Generated compact data file (see Build)
├── build_frontend.py             # Script that generates voyd_data.json
├── requirements.txt              # Python dependencies
├── start.sh                      # Dev server launcher
└── venv/                         # Python virtual environment
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

### Start backend dev server
```bash
./start.sh
```
Runs `uvicorn engine.main:app --host 127.0.0.1 --port 8765 --reload`.

The script sources `~/.hermes/.env` to load `ANTHROPIC_API_KEY` into the environment before starting.

### Run backend manually
```bash
python3 -m uvicorn engine.main:app --host 127.0.0.1 --port 8765 --reload
```

---

## Runtime Architecture

### Backend (`engine/main.py`)
- FastAPI app with lifespan manager.
- Endpoints:
  - `POST /api/chat` — Main interaction. Accepts `session_id`, `message`, `model`. Returns generated Voyd response, node metadata, termination flag, and glyph seed.
  - `GET /api/session/{session_id}` — Retrieve session state.
  - `GET /api/glyph/{session_id}` — Retrieve glyph generation data for the session.
  - `GET /api/health` — Health check including whether the API key is configured.
- CORS is enabled with `allow_origins=["*"]`. A comment notes this should be restricted in production.
- Sessions are stored in an in-memory dictionary (`self.sessions` in `NarrativeEngine`). They are lost on server restart.
- The backend calls the Anthropic Messages API server-side, using the last 6 turns of history for context (`max_tokens: 300`).
- If the API call fails or no key is configured, it falls back to the node's `content_template`.

### Frontend (`frontend/index.html` + `voyd_engine.js`)
- Loads `voyd_data.json` at boot and instantiates `VoydEngine`.
- The UI is immersive and atmospheric: black background, custom cursor, letter-level physics (mouse repulsion), ambient audio, and a seeded SVG glyph shown at session end.
- User input is captured via a hidden input field; typed text is mirrored into a styled preview.
- Voyd responses are rendered character-by-character with variable timing.
- If `API_BASE` is set (via `localStorage` key `voyd_api`), the frontend calls the backend proxy.
- Otherwise, if `ANTHROPIC_API_KEY` is set (via `localStorage` key `voyd_key`), it calls Anthropic directly from the browser.
- If neither is available, it falls back to `content_template`.

### Narrative Engine (`engine/narrative_engine.py` and `frontend/voyd_engine.js`)
Both implementations share the same logic:
- **Nodes** have types: `threshold`, `dialogue`, `revelation`, `choice`, `terminus`.
- **Intent classification** maps player text to one of: `inquiry`, `confession`, `challenge`, `silence`, plus a topic.
- **Emotional vector** tracks `surrender`, `defiance`, `curiosity` (0.0–1.0). Values shift per turn and decay slightly.
- **Transition selection** evaluates conditions against intent, topic, depth, and emotional state. Unvisited nodes are preferred. Dead-ends fall back to `gravity` or `choice`.
- **System prompt construction** builds a highly specific persona prompt for Claude, embedding lore fragments and current node state. The prompt enforces lowercase output, dream-logic, sentence count limits, and banned phrases.

### Lore Index (`engine/lore_index.py`)
- Scans markdown and text files under `/home/patrick/Gate_of_Nyandor` (the project's external wiki/novel source material).
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
Generated by `build_frontend.py`. Same shape as `story_graph.json` but with `lore_map` attached (topic → lore chunks). Used by the client-side engine.

---

## Code Style Guidelines

- Python: standard style, docstrings on modules and classes, type hints used sparingly.
- JavaScript: ES6 classes, camelCase for methods/properties, snake_case in JSON keys to match Python.
- Comments and documentation are in English.
- The Voyd's voice uses a deliberate lowercase aesthetic with unconventional punctuation. This is enforced in the system prompt, not in code.

---

## Security Considerations

- `ANTHROPIC_API_KEY` is loaded from `~/.hermes/.env` or the environment. Never commit it.
- The backend keeps the key server-side. The frontend's direct-Anthropic mode (`localStorage.getItem('voyd_key')`) is explicitly marked as "only for private/testing" in the code.
- CORS is wide open (`allow_origins=["*"]`). Restrict this before deploying to production.
- Session state is held in memory; there is no authentication or authorization.

---

## Testing

There is no test suite, test framework, or CI configuration in this project. Testing is manual via browser interaction and backend health checks (`/api/health`).

---

## Deployment Notes

- The frontend is designed to be served statically (e.g., GitHub Pages).
- The backend is a single-process FastAPI app suitable for running behind a reverse proxy.
- There is no Docker configuration, no production WSGI/ASGI server setup beyond Uvicorn, and no database.

---

## Testing Protocol

Run these steps before every commit and push. Do not push if any step fails.

1. Start the dev server: `./start.sh` — confirm it starts without errors
2. Health check: `curl http://localhost:8765/api/health` — must return 200
3. Graph integrity: load `data/act1_nodes.json` and walk every path from node `1.0` to node `10.0` — confirm every `next` pointer resolves and no dead ends exist
4. Act 1 traversal: simulate all four archetype paths (person_present, person_gone, self_regret, self_unlived) and confirm `portalValue`, `archetype`, and `playerAnswer` are set correctly at node `10.0`
5. Act 2 handoff: confirm the session state carrying those three values reaches the system prompt builder in `voyd_engine.js`
6. If all pass: `git add -A && git commit -m "<message>" && git push origin main`
7. If any fail: report exactly what broke. Do not touch git.
