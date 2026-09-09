"""Plates illustrate the scene's turn, and never gate the story.

The contract these tests hold:
  * a plate is OPTIONAL -- a scene without one must still publish, so there is
    deliberately no test demanding full coverage;
  * a plate must belong to a real scene (an orphan would ship bytes the reader
    can never show);
  * every scene must yield a substantive inflection moment, because that is
    what the renderer draws. A scene that yields nothing would silently get
    scenery instead of its turn.
"""
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCENES = ROOT / "story" / "scenes"
IMAGES = ROOT / "story" / "images"

sys.path.insert(0, str(ROOT / "scripts"))
from render_scene_image import inflection_moment  # noqa: E402


class SceneImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = {p.stem for p in SCENES.glob("*.md")}
        cls.plates = {p.stem for p in IMAGES.glob("*.webp")}
        cls.sidecars = sorted(IMAGES.glob("*.json"))

    def test_every_plate_belongs_to_a_real_scene(self):
        orphans = sorted(self.plates - self.scenes)
        self.assertEqual(
            [], orphans,
            "a plate exists for a scene that does not: the reader can never "
            "show it. Delete it, or restore the scene.",
        )

    def test_a_scene_without_a_plate_is_allowed(self):
        # Encoded as a test so nobody later "fixes" partial coverage by making
        # it mandatory. Art failing must never stop the fiction from shipping.
        self.assertTrue(self.scenes, "there are no scenes at all")

    def test_every_scene_yields_an_inflection_moment(self):
        thin = []
        for p in sorted(SCENES.glob("*.md")):
            moment = inflection_moment(p.read_text(encoding="utf-8"))
            if len(moment) < 120:
                thin.append(f"{p.stem} -> {moment!r}")
        self.assertEqual(
            [], thin,
            "a scene yields no usable turn, so its plate would be drawn from "
            "scenery instead of its change of state.",
        )

    def test_sidecars_are_valid_and_match_their_scene(self):
        bad = []
        for s in self.sidecars:
            try:
                data = json.loads(s.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                bad.append(f"{s.name}: unreadable ({e})")
                continue
            if data.get("scene") != s.stem:
                bad.append(f"{s.name}: records scene {data.get('scene')!r}")
            if not data.get("moment"):
                bad.append(f"{s.name}: no moment recorded")
        self.assertEqual([], bad)


if __name__ == "__main__":
    unittest.main()
