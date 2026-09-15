import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    spec = importlib.util.spec_from_file_location(
        "run_story_room_v3", ROOT / "scripts" / "run_story_room.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StoryRoomV3RunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = load_runner()

    def test_prompt_contains_v3_lore_state_and_publication_contracts(self):
        with mock.patch.object(self.r, "load_resume", return_value=None):
            prompt = self.r.build_prompt(Path("/tmp/packet.json"), "abc123")
        self.assertIn("lore/canon/CORE_LAWS.md", prompt)
        self.assertIn("story_room/state/frontiers.json", prompt)
        self.assertIn("550 prose words", prompt)
        self.assertIn("may NOT reduce the number of reachable live leaves", prompt)
        self.assertIn("independent Prose Editor", prompt)
        self.assertIn("validate_story_v3.py --base abc123", prompt)
        self.assertIn("UNATTENDED TOOL SAFETY", prompt)
        self.assertIn("Make up to THREE implementation/replay attempts", prompt)

    def test_primary_route_precedes_real_local_qwen_fallback(self):
        passed = {
            "status": "passed",
            "human_input_required": False,
            "final_replay": "passed",
            "summary": "ok",
        }
        with tempfile.TemporaryDirectory() as tmp, \
             mock.patch.object(self.r, "STATUS_PATH", Path(tmp) / "status.json"), \
             mock.patch.object(self.r, "require_sync_hook"), \
             mock.patch.object(self.r, "build_packet", return_value=Path("/tmp/p.json")), \
             mock.patch.object(self.r, "build_prompt", return_value="prompt"), \
             mock.patch.object(self.r, "run_hermes", side_effect=[1, 0]) as run_hermes, \
             mock.patch.object(self.r, "read_status", side_effect=[None, passed]), \
             mock.patch.object(self.r, "clean_partial_attempt"), \
             mock.patch.object(self.r, "note_route") as note_route:
            rc = self.r.run(20)

        self.assertEqual(rc, 0)
        self.assertEqual(run_hermes.call_count, 2)
        self.assertNotIn("provider", run_hermes.call_args_list[0].kwargs)
        self.assertEqual(run_hermes.call_args_list[1].kwargs["provider"], self.r.LOCAL_PROVIDER)
        note_route.assert_called_once_with(self.r.LOCAL_PROVIDER)


if __name__ == "__main__":
    unittest.main()
