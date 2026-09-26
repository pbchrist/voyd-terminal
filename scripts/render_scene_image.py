#!/usr/bin/env python3
"""Render one scene's inflection moment as a plate for the reader.

The image is the scene's TURN -- the instant the state changes -- not its
scenery. Every scene in this corpus lands its turn in the last prose block
before the choices, so that is what we draw when no explicit moment is given.

Art never gates the story. If ComfyUI is down, or a render fails, this exits
non-zero for the ONE scene and the cycle publishes the fiction without it; a
later cycle retries. Nothing here may raise into the story commit.

Usage:
    render_scene_image.py <scene.md> [--moment "..."] [--force]
    render_scene_image.py --all [--force]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = ROOT / "story" / "scenes"
IMAGES = ROOT / "story" / "images"
API = "http://127.0.0.1:8188"
CKPT = "flux1-dev-fp8.safetensors"

# One look for the whole corpus. Faelspire is a city of cats, and the fiction
# is records, doors and filed frames -- an engraved plate suits both, and keeps
# anthropomorphic figures legible instead of uncanny (flux has no character
# LoRA here, so identity must ride on silhouette and situation, never a face).
# MEDIUM ONLY. Nothing here may describe a setting, a costume, or a camera.
#
# The first version of this constant carried ~800 characters of setting and
# blocking -- "worn medieval dress", "seen at a distance or from behind",
# "iron doors, archive racks, ledgers" -- in front of every moment. The result
# was 23 variations of one prompt: robed figures in arched stone, in every
# scene, regardless of what actually happened in it. A scene whose turn was
# "every rooftop cat begins screaming, the sliver ignites orange in his paw"
# rendered as monks in a cloister.
#
# The moment decides the picture. Style only says how it is drawn.
# Style may describe INK, never light, setting, costume or camera.
#
# Two failures are baked into this constant's history. First it carried the
# setting ("iron doors, archive racks") and the camera ("seen from behind"),
# and every scene rendered as the same room. Removing that fixed it. Then a
# "tonal" anchor -- heavy blacks, DEEP SHADOW, dark inked plate -- put the
# room back: lighting words imply dim interiors, dim interiors imply stone,
# stone implies archways, and the procession-of-lights scene became a robed
# cat in a hall again.
#
# So: density of ink is safe to enforce. Darkness of the depicted world is
# not, because it is a fact about the scene, and the scene is the moment's
# to decide.
STYLE = (
    "Engraved etching illustration, dense crosshatching, fine ink linework, "
    "strong black ink, monochrome, no colour. "
    "The characters are anthropomorphic cats."
)

CHOICE = re.compile(r"^###\s*\[.*?\]\(.*?\.md\)", re.M)
HEADING = re.compile(r"^#{1,6}\s")
FRONTIER = re.compile(r"^##\s*(?:◉\s*)?ACTIVE FRONTIER", re.M)
RULE = re.compile(r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$")


def inflection_moment(body: str) -> str:
    """The last prose block before the scene stops advancing.

    Choices, frontier notes and headings are machinery, not fiction. What
    remains, last-first, is the landing beat -- the changed state.
    """
    cut = len(body)
    for pat in (CHOICE, FRONTIER):
        m = pat.search(body)
        if m:
            cut = min(cut, m.start())
    blocks = []
    for b in body[:cut].split("\n\n"):
        b = b.strip()
        if not b or HEADING.match(b) or RULE.match(b):
            continue
        blocks.append(b)
    if not blocks:
        return ""
    # The turn is the landing beat, but this corpus lands hard and short
    # ("The name is burning."). A single line is a statement, not a picture --
    # fold earlier blocks in until there is enough to compose from.
    picked: list[str] = []
    for b in reversed(blocks):
        picked.insert(0, b)
        if len(" ".join(picked)) >= 220:
            break
    return " ".join(" ".join(picked).split())[:700]


def workflow(prompt: str, seed: int) -> dict:
    return {
        "1": {"class_type": "CheckpointLoaderSimple",
              "inputs": {"ckpt_name": CKPT}},
        "2": {"class_type": "CLIPTextEncode",
              "inputs": {"text": prompt, "clip": ["1", 1]}},
        "3": {"class_type": "FluxGuidance",
              "inputs": {"conditioning": ["2", 0], "guidance": 3.5}},
        "4": {"class_type": "CLIPTextEncode",
              "inputs": {"text": "", "clip": ["1", 1]}},
        "5": {"class_type": "EmptySD3LatentImage",
              "inputs": {"width": 1024, "height": 640, "batch_size": 1}},
        "6": {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": 20, "cfg": 1.0,
                         "sampler_name": "euler", "scheduler": "simple",
                         "denoise": 1.0, "model": ["1", 0],
                         "positive": ["3", 0], "negative": ["4", 0],
                         "latent_image": ["5", 0]}},
        "7": {"class_type": "VAEDecode",
              "inputs": {"samples": ["6", 0], "vae": ["1", 2]}},
        "8": {"class_type": "SaveImage",
              "inputs": {"images": ["7", 0], "filename_prefix": "voyd"}},
    }


def _post(path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        API + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=30))


def _get(path: str) -> dict:
    return json.load(urllib.request.urlopen(API + path, timeout=30))


def render(scene: Path, moment: str = "", force: bool = False) -> bool:
    stem = scene.stem
    out = IMAGES / f"{stem}.webp"
    side = IMAGES / f"{stem}.json"
    if out.exists() and not force:
        print(f"skip {stem}: already has a plate")
        return True

    body = scene.read_text(encoding="utf-8")
    moment = moment or inflection_moment(body)
    if not moment:
        print(f"skip {stem}: no inflection moment found")
        return False

    # A stable seed per scene: re-rendering a scene keeps its composition
    # unless the moment itself changed.
    seed = int(uuid.uuid5(uuid.NAMESPACE_URL, stem).int % 2**31)
    # Moment FIRST. A style prefix dominates what the model draws; the scene's
    # turn has to be the subject, not a suffix appended to a house style.
    prompt = f"{moment} -- {STYLE}"

    try:
        pid = _post("/prompt", {"prompt": workflow(prompt, seed),
                                "client_id": str(uuid.uuid4())})["prompt_id"]
    except (urllib.error.URLError, OSError, KeyError) as e:
        print(f"FAIL {stem}: ComfyUI unreachable ({e}); story publishes without art")
        return False

    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(3)
        try:
            hist = _get(f"/history/{pid}")
        except (urllib.error.URLError, OSError):
            continue
        if pid not in hist:
            continue
        imgs = hist[pid].get("outputs", {}).get("8", {}).get("images", [])
        if not imgs:
            print(f"FAIL {stem}: render produced no image")
            return False
        info = imgs[0]
        url = (f"/view?filename={info['filename']}"
               f"&subfolder={info.get('subfolder','')}"
               f"&type={info.get('type','output')}")
        data = urllib.request.urlopen(API + url, timeout=120).read()
        IMAGES.mkdir(parents=True, exist_ok=True)
        tmp = IMAGES / f"{stem}.png"
        tmp.write_bytes(data)
        try:
            from PIL import Image
            im = Image.open(tmp)
            im.save(out, "WEBP", quality=82, method=6)
            tmp.unlink()
        except Exception as e:                      # Pillow missing or bad file
            print(f"FAIL {stem}: could not encode webp ({e})")
            tmp.unlink(missing_ok=True)
            return False
        side.write_text(json.dumps(
            {"scene": stem, "moment": moment, "seed": seed,
             "style": STYLE.strip()}, indent=1) + "\n", encoding="utf-8")
        print(f"ok   {stem}: {out.stat().st_size // 1024} KB")
        return True

    print(f"FAIL {stem}: render timed out")
    return False


def prune_orphans() -> int:
    """Drop plates whose scene no longer exists.

    A hone cycle may legitimately delete a scene (merging a near-duplicate,
    say). Its plate must go with it -- but quietly, as cleanup. On 2026-09-08
    a leftover plate failed a test and cost a whole cycle's work; nothing
    about an image may ever fail a story night again.
    """
    if not IMAGES.exists():
        return 0
    scenes = {p.stem for p in SCENES.glob("*.md")}
    dropped = 0
    for p in sorted(IMAGES.iterdir()):
        if p.suffix in {".webp", ".json"} and p.stem not in scenes:
            p.unlink()
            print(f"prune {p.name}: scene no longer exists")
            dropped += 1
    return dropped


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", nargs="?")
    ap.add_argument("--moment", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--prune", action="store_true",
                    help="drop plates whose scene is gone, then exit")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()

    if a.prune and not (a.all or a.scene):
        print(f"pruned {prune_orphans()}")
        return 0

    if a.all:
        prune_orphans()
        targets = sorted(SCENES.glob("*.md"))
    elif a.scene:
        p = Path(a.scene)
        targets = [p if p.is_absolute() else SCENES / Path(a.scene).name]
    else:
        ap.error("give a scene or --all")

    ok = sum(render(t, a.moment, a.force) for t in targets)
    print(f"\n{ok}/{len(targets)} plates present")
    # Art is never a gate: a partial run is still a successful run.
    return 0


if __name__ == "__main__":
    sys.exit(main())
