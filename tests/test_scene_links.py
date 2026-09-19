"""The reader is the product: every scene link must resolve, and a scene must
declare itself either finished (choice links) or open (an ACTIVE FRONTIER
block), never both.

This mirrors the gate in .github/workflows/story-pages.yml so a cycle fails
locally, before commit, instead of pushing a commit that cannot publish.
"""
import pathlib
import re
import unittest

SCENES = pathlib.Path(__file__).resolve().parent.parent / "story" / "scenes"
LINK = re.compile(r"\]\(([^)]+\.md)\)")
CHOICE = re.compile(r"^###\s*\[.*?\]\(([^)]+\.md)\)", re.M)


class SceneLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = sorted(SCENES.glob("*.md"))
        cls.have = {p.name for p in cls.files}
        cls.text = {p.name: p.read_text(encoding="utf-8") for p in cls.files}

    def test_every_choice_resolves_to_a_real_scene(self):
        bad = [
            f"{name} -> {target}"
            for name, body in self.text.items()
            for target in LINK.findall(body)
            if target not in self.have
        ]
        self.assertEqual(
            [], bad,
            "a scene links to a file that does not exist. A scene that has not "
            "been written yet is an ACTIVE FRONTIER block, never a choice link.",
        )

    def test_a_scene_is_either_open_or_finished_never_both(self):
        bad = [
            name for name, body in self.text.items()
            if "ACTIVE FRONTIER" in body and CHOICE.search(body)
        ]
        self.assertEqual(
            [], bad,
            "a scene carries both an ACTIVE FRONTIER block and a choice link. "
            "The reader parses everything after the frontier heading as the "
            "frontier note, so the choice is swallowed and the path reads as a "
            "dead end. Extending a frontier must remove the block.",
        )


if __name__ == "__main__":
    unittest.main()
