import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_story_v3", ROOT / "scripts" / "validate_story_v3.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StoryV3ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = load_validator()

    def test_rejects_direct_collapse_of_prior_live_leaves(self):
        prior = {"000-the-fourth-bell.md": ["a.md", "b.md"], "a.md": [], "b.md": []}
        current = {**prior, "a.md": ["new.md"], "b.md": ["new.md"], "new.md": []}
        with mock.patch.object(self.v, "graph_at", return_value=prior):
            errors = self.v.branch_collapse_errors(current, "HEAD")
        self.assertEqual(len(errors), 1)
        self.assertIn("a.md, b.md", errors[0])
    def test_allows_separate_extensions(self):
        prior = {"000-the-fourth-bell.md": ["a.md", "b.md"], "a.md": [], "b.md": []}
        current = {
            **prior,
            "a.md": ["a-next.md"],
            "b.md": ["b-next.md"],
            "a-next.md": [],
            "b-next.md": [],
        }
        with mock.patch.object(self.v, "graph_at", return_value=prior):
            self.assertEqual(self.v.branch_collapse_errors(current, "HEAD"), [])

    def test_frontier_ledger_must_equal_reachable_leaves(self):
        graph = {"start.md": ["a.md", "b.md"], "a.md": [], "b.md": []}
        with tempfile.TemporaryDirectory() as tmp:
            frontier = Path(tmp) / "frontier.json"
            frontier.write_text(json.dumps({
                "canonical_entry": "story/scenes/start.md",
                "active_frontiers": [{"path": "story/scenes/a.md"}],
            }))
            with mock.patch.object(self.v, "FRONTIER", frontier):
                errors = self.v.frontier_errors(graph)
        self.assertEqual(len(errors), 1)
        self.assertIn("b.md", errors[0])


if __name__ == "__main__":
    unittest.main()
