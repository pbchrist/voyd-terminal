import importlib.util
import types
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_supervisor():
    spec = importlib.util.spec_from_file_location(
        "autonomous_story_room_retry", ROOT / "scripts" / "autonomous_story_room.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StoryRoomRetryPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = load_supervisor()

    def common_patches(self):
        return (
            mock.patch.object(self.a, "ensure_clean_and_synced"),
            mock.patch.object(self.a, "PENDING_PATH", Path("/tmp/voyd-no-pending-speciation-test.json")),
            mock.patch.object(self.a, "git", return_value=types.SimpleNamespace(stdout="abc123\n")),
            mock.patch.object(self.a, "visible_post"),
            mock.patch.object(self.a, "discard_incomplete_run"),
            mock.patch.object(self.a, "write_public_status"),
            mock.patch.object(self.a, "commit_status_only"),
            mock.patch.object(self.a, "log"),
        )

    def test_process_crash_requests_systemd_retry(self):
        patches = self.common_patches()
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], \
             mock.patch.object(self.a, "run", return_value=types.SimpleNamespace(returncode=1)):
            rc = self.a.one_cycle()
        self.assertEqual(rc, self.a.TECHNICAL_RETRY_EXIT)

    def test_blocked_verdict_requests_systemd_retry(self):
        patches = self.common_patches()
        blocked = {
            "status": "blocked", "human_input_required": False,
            "final_replay": "blocked", "summary": "provider unavailable",
        }
        with patches[0], patches[1], patches[2], patches[3], patches[4], patches[5], patches[6], patches[7], \
             mock.patch.object(self.a, "run", return_value=types.SimpleNamespace(returncode=0)), \
             mock.patch.object(self.a, "load_status", return_value=blocked):
            rc = self.a.one_cycle()
        self.assertEqual(rc, self.a.TECHNICAL_RETRY_EXIT)

    def test_systemd_restarts_retryable_failure(self):
        unit = (ROOT / "systemd" / "voyd-story-room.service").read_text()
        self.assertIn("Restart=on-failure", unit)
        self.assertIn("RestartSec=30min", unit)
        self.assertIn("StartLimitIntervalSec=0", unit)


if __name__ == "__main__":
    unittest.main()
