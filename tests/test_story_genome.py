import tempfile
import unittest
from pathlib import Path

from story_room.genome import GenomeStore
from story_room.speciation import decide_speciation


class StoryGenomeTests(unittest.TestCase):
    def test_inferred_law_requires_repeat_before_activation(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = GenomeStore(Path(tmp) / "genome.json")
            first = store.observe_law(statement="Scenes must alter the next scene.", kind="require",
                                      scopes=["scene"], decision_id="d1")
            self.assertEqual(first["status"], "candidate")
            second = store.observe_law(statement="Scenes must alter the next scene.", kind="require",
                                       scopes=["scene"], decision_id="d2")
            self.assertEqual(second["status"], "active")

    def test_explicit_law_activates_immediately(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = GenomeStore(Path(tmp) / "genome.json")
            law = store.observe_law(statement="Every scale is dialectical.", kind="require",
                                    scopes=["line", "scene", "act"], decision_id="d1", explicit=True)
            self.assertEqual(law["status"], "active")
            self.assertEqual(law["origin"], "explicit")

    def test_human_gate_when_two_viable_futures_survive(self):
        candidates = [
            {"id": "a", "title": "A", "structurally_viable": True, "story_consequence": "Soryn is responsible"},
            {"id": "b", "title": "B", "structurally_viable": True, "story_consequence": "Soryn is complicit"},
        ]
        result = decide_speciation(candidates, [])
        self.assertEqual(result["mode"], "human")
        self.assertEqual(len(result["fork"]), 2)

    def test_active_hard_law_can_choose_without_human(self):
        laws = [{"id": "law_x", "kind": "require", "status": "active"}]
        candidates = [
            {"id": "a", "structurally_viable": True},
            {"id": "b", "structurally_viable": True, "violates_law_ids": ["law_x"]},
        ]
        result = decide_speciation(candidates, laws)
        self.assertEqual(result["mode"], "auto")
        self.assertEqual(result["selected"], "a")


if __name__ == "__main__":
    unittest.main()
