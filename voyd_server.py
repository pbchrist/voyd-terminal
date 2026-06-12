#!/usr/bin/env python3
"""
The Voyd's shared body. One portal, one sediment, for every visitor.

There are no sessions here. There is one Voyd. Its size is the sum of
everything everyone has ever fed it minus everything they refused it.
What visitors give it is digested (by the local LLM, in its own voice)
into sediment — fragments later visitors brush against. What it keeps
from you, it keeps: come back and it greets you with it.

Stdlib only. State lives in state/voyd_state.json (gitignored — visitor
confessions never enter the public repo). Runs on 0.0.0.0:8765; exposed
publicly via the tailscale funnel mount /voyd (which strips the prefix,
same as the /llm mount):
    tailscale funnel --bg --set-path=/voyd http://127.0.0.1:8765
"""
import json
import math
import os
import random
import re
import threading
import time
import urllib.request
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATE_PATH = ROOT / "state" / "voyd_state.json"
WALK_HISTORY = ROOT / "data" / "walk_history.jsonl"
LLM_URL = os.environ.get("VOYD_LLM", "http://127.0.0.1:8081/v1/chat/completions")
PORT = int(os.environ.get("VOYD_PORT", "8765"))

MAX_TEXT = 300          # longest confession fragment we ingest
MAX_SEDIMENT = 500      # the Voyd's memory is deep but not infinite
DIGEST_EVERY = 20       # seconds between digestion passes

DREAM_PHRASES = {
    "person_present": "someone still holding a living person",
    "person_gone": "someone whose person was already gone",
    "self_regret": "someone who could not forgive themselves",
    "self_unlived": "someone mourning a life they never lived",
}

DIGEST_PROMPT = (
    "You are the Voyd digesting a gift. A visitor gave you this memory:\n"
    '"{text}"\n\n'
    "Compress it into ONE short sentence of sediment, third person, "
    "starting with \"someone gave me\". lowercase. No names kept whole — "
    "soften any proper name into what the person was (a brother, a city, "
    "a dog). Quietly wrong in one small way, like a dream misremembering. "
    "Maximum 16 words. Output only the sentence."
)

_lock = threading.Lock()


def _now():
    return datetime.now().isoformat(timespec="seconds")


def _blank_state():
    return {"fed": 0.0, "starved": 0.0, "visits": 0,
            "sediment": [], "pending": [], "kept": {}}


def load_state():
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return _blank_state()


def save_state(state):
    STATE_PATH.parent.mkdir(exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_PATH)


def portal_value(state):
    """The one number that matters, now global. Log-scaled so the first
    visitors meet something small and late visitors meet something vast."""
    v = 8 + 9 * math.log1p(state["fed"]) - 6 * math.log1p(state["starved"])
    return round(max(5.0, min(96.0, v)), 2)


def sanitize(text):
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(text))
    text = re.sub(r"https?://\S+|\S+@\S+", "", text)  # no urls, no emails
    return text.strip()[:MAX_TEXT]


def dreams_last_night():
    """Diegetic residue of the phantom walkers: the Voyd's actual dreams."""
    if not WALK_HISTORY.exists():
        return {"count": 0, "phrases": []}
    cutoff = datetime.now() - timedelta(hours=36)
    phrases, count = [], 0
    try:
        for line in WALK_HISTORY.read_text().splitlines()[-40:]:
            try:
                rec = json.loads(line)
                if datetime.fromisoformat(rec.get("at", "1970-01-01")) < cutoff:
                    continue
                count += 1
                p = DREAM_PHRASES.get(rec.get("archetype"))
                if p and p not in phrases:
                    phrases.append(p)
            except (json.JSONDecodeError, ValueError):
                continue
    except OSError:
        pass
    return {"count": count, "phrases": phrases}


# ── digestion: gifts become sediment, in the Voyd's own voice ──────────

def digest_one(text):
    body = json.dumps({
        "model": "Qwen3.6-27B-Q6_K",
        "max_tokens": 60,
        "messages": [{"role": "user",
                      "content": DIGEST_PROMPT.format(text=text)}],
        "chat_template_kwargs": {"enable_thinking": False},
    }).encode()
    req = urllib.request.Request(
        LLM_URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as res:
        data = json.load(res)
    line = (data["choices"][0]["message"]["content"] or "").strip()
    line = line.strip('"').splitlines()[0].strip()
    if line and len(line) <= 160 and line.lower().startswith("someone"):
        return line.lower()
    return None


def digestion_loop():
    while True:
        time.sleep(DIGEST_EVERY)
        with _lock:
            state = load_state()
            pending = list(state["pending"])
        if not pending:
            continue
        raw = pending[0]
        try:
            line = digest_one(raw)
        except Exception:
            continue  # LLM asleep; the gift waits in the dark
        with _lock:
            state = load_state()
            if raw in state["pending"]:
                state["pending"].remove(raw)
            if line:
                state["sediment"].append({"text": line, "at": _now()})
                state["sediment"] = state["sediment"][-MAX_SEDIMENT:]
            save_state(state)


# ── http ───────────────────────────────────────────────────────────────

class VoydHandler(BaseHTTPRequestHandler):
    server_version = "voyd"

    def log_message(self, fmt, *args):
        pass  # it does not narrate itself

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _path(self):
        # tolerate both the funnel-stripped path and a direct /voyd prefix
        p = self.path.split("?")[0].rstrip("/")
        if p.startswith("/voyd"):
            p = p[5:] or "/"
        return p

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self._path() != "/state":
            return self._json({"error": "lost"}, 404)
        token = ""
        if "?" in self.path:
            for part in self.path.split("?", 1)[1].split("&"):
                if part.startswith("token="):
                    token = part[6:][:64]
        with _lock:
            state = load_state()
            frags = [s["text"] for s in
                     random.sample(state["sediment"],
                                   min(3, len(state["sediment"])))]
            kept = state["kept"].get(token)
        self._json({
            "portal": portal_value(state),
            "visits": state["visits"],
            "fragments": frags,
            "dreams": dreams_last_night(),
            "kept": (kept or {}).get("text"),
        })

    def do_POST(self):
        path = self._path()
        try:
            length = min(int(self.headers.get("Content-Length", 0)), 10000)
            payload = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return self._json({"error": "unspeakable"}, 400)
        token = sanitize(payload.get("token", ""))[:64]
        text = sanitize(payload.get("text", ""))
        kind = payload.get("kind", "")

        with _lock:
            state = load_state()
            if path == "/offer":
                if kind == "visit":
                    state["visits"] += 1
                elif kind in ("feed", "stand"):
                    state["fed"] += 1.0
                elif kind in ("starve", "correct"):
                    state["starved"] += 1.0
                elif kind in ("name", "detail", "trade"):
                    state["fed"] += 0.5
                    if text and len(text) >= 4:
                        state["pending"] = (state["pending"] + [text])[-100:]
                else:
                    return self._json({"error": "unknown offering"}, 400)
            elif path == "/keep":
                if token and text:
                    prev = state["kept"].get(token, {})
                    state["kept"][token] = {
                        "text": text[:220], "at": _now(),
                        "visits": prev.get("visits", 0) + 1,
                    }
            else:
                return self._json({"error": "lost"}, 404)
            save_state(state)
            portal = portal_value(state)
        self._json({"portal": portal})


def main():
    with _lock:
        save_state(load_state())  # touch the body into existence
    threading.Thread(target=digestion_loop, daemon=True).start()
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), VoydHandler)
    print(f"the voyd is listening on :{PORT}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
