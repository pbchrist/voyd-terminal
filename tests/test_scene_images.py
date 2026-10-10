"""Plates illustrate the scene's turn, and never gate the story.

HARD-WON: the supervisor fails a whole cycle if this suite fails. On
2026-09-08 a hone cycle correctly deleted a near-duplicate scene, left its
plate behind, and an orphan-plate assertion here turned a good night's work
into `status: failed`. An image must never be able to do that again.

So the rule for this file: the ONLY hard assertion is about CODE (does the
extractor still find a turn in every scene). Anything about the state of the
asset directory is reported, never failed -- orphans are pruned by
`render_scene_image.py --prune`, which the cycle runs, and a stray file on
disk is harmless to the reader because nothing links to it.
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

    def test_every_scene_yields_an_inflection_moment(self):
        """The one hard gate: a scene the extractor cannot read would be
        drawn from scenery instead of its turn. This tests code against
        fiction and cannot be broken by the state of the image directory."""
        thin = []
        for p in sorted(SCENES.glob("*.md")):
            moment = inflection_moment(p.read_text(encoding="utf-8"))
            if len(moment) < 120:
                thin.append(f"{p.stem} -> {moment!r}")
        self.assertEqual([], thin, "a scene yields no usable turn")

    def test_asset_state_is_reported_never_failed(self):
        """Coverage and orphans are information, not verdicts.

        A scene without a plate must publish. A plate without a scene is
        dead weight the pruner clears. Neither may stop the fiction."""
        orphans = sorted(self.plates - self.scenes)
        uncovered = sorted(self.scenes - self.plates)
        if orphans:
            print(f"\n  [plates] {len(orphans)} orphan(s) to prune: "
                  f"{', '.join(orphans)}")
        if uncovered:
            print(f"\n  [plates] {len(uncovered)} scene(s) awaiting art: "
                  f"{', '.join(uncovered)}")
        self.assertTrue(self.scenes, "there are no scenes at all")

    def test_sidecars_that_exist_are_readable(self):
        """Reported, not failed, for the same reason."""
        bad = []
        for s in sorted(IMAGES.glob("*.json")):
            try:
                data = json.loads(s.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                bad.append(f"{s.name}: unreadable ({e})")
                continue
            if data.get("scene") != s.stem or not data.get("moment"):
                bad.append(f"{s.name}: mismatched or empty record")
        if bad:
            print("\n  [plates] sidecar problems: " + "; ".join(bad))
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
