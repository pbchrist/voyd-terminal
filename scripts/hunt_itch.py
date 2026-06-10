#!/usr/bin/env python3
"""Weekly itch.io hunt: find top Twine games, parse passage graphs,
and extract structural patterns to update the Voyd rubric."""

from __future__ import annotations

import json
import re
import textwrap
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RUBRIC_PATH = REPO_ROOT / "data" / "rubric.json"
LOG_PATH = REPO_ROOT / "logs" / "hunt_itch.log"
QWEN_BASE_URL = "http://localhost:8081/v1"
QWEN_MODEL = "Qwen3.6-27B-Q6_K"

ITCH_LISTING = "https://itch.io/games/top-rated/platform-web/tag-interactive-fiction"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VoydTerminal/1.0)"}


def log(msg: str) -> None:
    line = f"[{__import__('datetime').datetime.now().isoformat()}] {msg}"
    print(line)
    LOG_PATH.parent.mkdir(exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def extract_game_urls(html: str) -> list[str]:
    """Extract game page URLs from the itch.io listing."""
    urls = set()
    for m in re.finditer(r'href="(/games/[^"]+)"', html):
        path = m.group(1)
        if "?" not in path:
            urls.add(f"https://itch.io{path}")
    return sorted(urls)[:20]  # Limit to first 20


def is_twine(html: str) -> bool:
    return "<tw-storydata" in html or "data-passage" in html or "tw-passagedata" in html


def extract_twine_data(html: str) -> dict[str, Any] | None:
    """Extract tw-storydata and passages from raw HTML."""
    match = re.search(r"(<tw-storydata[^>]*>.*?</tw-storydata>)", html, re.DOTALL)
    if not match:
        return None
    xml = match.group(1)
    passages: list[dict[str, Any]] = []
    startnode = re.search(r'startnode="(\d+)"', xml)
    start_pid = int(startnode.group(1)) if startnode else None

    for m in re.finditer(r'<tw-passagedata[^>]*pid="(\d+)"[^>]*name="([^"]*)"[^>]*>(.*?)</tw-passagedata>', xml, re.DOTALL):
        pid, name, text = m.groups()
        passages.append({
            "pid": int(pid),
            "name": name,
            "text": text.strip(),
        })

    if not passages:
        return None

    return {
        "passage_count": len(passages),
        "start_pid": start_pid,
        "passages": passages,
    }


def parse_passage_links(text: str) -> list[str]:
    """Extract link targets from Twine passage text."""
    links = []
    # [[Target]] or [[Display->Target]] or [[Target|Display]]
    for m in re.finditer(r"\[\[(.+?)\]\]", text):
        link = m.group(1)
        if "->" in link:
            links.append(link.split("->", 1)[1].strip())
        elif "|" in link:
            links.append(link.split("|", 1)[0].strip())
        else:
            links.append(link.strip())
    return links


def build_graph(story: dict[str, Any]) -> dict[str, Any]:
    """Build a directed graph of passage links."""
    passages = {p["name"]: p for p in story["passages"]}
    graph = {name: {"to": [], "from": []} for name in passages}
    for p in story["passages"]:
        targets = parse_passage_links(p["text"])
        for t in targets:
            if t in graph:
                graph[p["name"]]["to"].append(t)
                graph[t]["from"].append(p["name"])
    return graph


def structural_summary(story: dict[str, Any], graph: dict[str, Any]) -> dict[str, Any]:
    """Compute basic structural metrics."""
    names = list(graph.keys())
    start_name = next((p["name"] for p in story["passages"] if p["pid"] == story.get("start_pid")), names[0])

    # BFS depth
    depths = {start_name: 0}
    queue = [start_name]
    while queue:
        current = queue.pop(0)
        for nxt in graph[current]["to"]:
            if nxt not in depths:
                depths[nxt] = depths[current] + 1
                queue.append(nxt)

    max_depth = max(depths.values()) if depths else 0
    avg_branching = sum(len(graph[n]["to"]) for n in names) / len(names) if names else 0
    convergence_points = [n for n in names if len(graph[n]["from"]) > 1]
    dead_ends = [n for n in names if not graph[n]["to"]]

    return {
        "passage_count": len(names),
        "max_depth": max_depth,
        "avg_branching": round(avg_branching, 2),
        "convergence_points": len(convergence_points),
        "dead_ends": len(dead_ends),
        "start": start_name,
    }


def qwen_chat(messages: list, max_tokens: int = 500, temperature: float = 0.7) -> str:
    payload = {
        "model": QWEN_MODEL,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
        "chat_template_kwargs": {"enable_thinking": False},
    }
    req = urllib.request.Request(
        f"{QWEN_BASE_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


def analyze_with_qwen(summary: dict[str, Any]) -> dict[str, Any]:
    prompt = textwrap.dedent(f"""\
        You are a narrative structural analyst. Analyze this Twine game graph:

        Passages: {summary['passage_count']}
        Max depth from start: {summary['max_depth']}
        Average branching: {summary['avg_branching']}
        Convergence points: {summary['convergence_points']}
        Dead ends: {summary['dead_ends']}

        Identify:
        1. Where is the thesis (setup)?
        2. Where is antithesis (complication/deepening)?
        3. Where is the turn?
        4. Where is catharsis or resolution?
        5. What structural technique makes this work?

        Return ONLY JSON:
        {{
          "patterns": ["...", "..."],
          "rubric_suggestions": {{"dialectic_function": "...", "tension_advancement": "...", "branch_choke_logic": "..."}}
        }}
    """)
    try:
        raw = qwen_chat([{"role": "user", "content": prompt}], max_tokens=400, temperature=0.7)
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        return json.loads(raw)
    except Exception as exc:
        log(f"Qwen analysis failed: {exc}")
        return {"patterns": [], "rubric_suggestions": {}}


def update_rubric(findings: list[dict[str, Any]]) -> None:
    if not RUBRIC_PATH.exists():
        log("Rubric not found; skipping update")
        return
    rubric = json.loads(RUBRIC_PATH.read_text(encoding="utf-8"))
    rubric.setdefault("external_analysis", []).append({
        "source": "itch.io_weekly_hunt",
        "games_analyzed": len(findings),
        "findings": findings,
    })
    RUBRIC_PATH.write_text(json.dumps(rubric, indent=2), encoding="utf-8")
    log("Updated rubric with external analysis")


def main() -> int:
    log("Starting itch.io hunt")
    try:
        listing_html = fetch(ITCH_LISTING)
    except Exception as exc:
        log(f"Failed to fetch listing: {exc}")
        return 1

    urls = extract_game_urls(listing_html)
    log(f"Found {len(urls)} game URLs")

    findings: list[dict[str, Any]] = []
    for url in urls:
        try:
            html = fetch(url)
            if not is_twine(html):
                continue
            story = extract_twine_data(html)
            if not story:
                continue
            graph = build_graph(story)
            summary = structural_summary(story, graph)
            log(f"Twine game {url}: {summary}")
            analysis = analyze_with_qwen(summary)
            findings.append({"url": url, "summary": summary, "analysis": analysis})
        except Exception as exc:
            log(f"Error processing {url}: {exc}")

    if findings:
        update_rubric(findings)
        log(f"Analyzed {len(findings)} Twine games")
    else:
        log("No Twine games found this week")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
