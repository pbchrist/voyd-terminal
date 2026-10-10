import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_installer():
    spec = importlib.util.spec_from_file_location(
        "install_hermes_story_room", ROOT / "scripts" / "install_hermes_story_room.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HermesStoryRoomInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_installer()

    def test_modern_hermes_needs_no_source_patch(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / "hermes-agent/hermes_cli").mkdir(parents=True)
            (home / "hermes-agent/tools").mkdir(parents=True)
            (home / "hermes-agent/hermes_cli/oneshot.py").write_text("declare_stateless_channel()\n")
            (home / "hermes-agent/tools/delegate_tool_dispatch.py").write_text("finite chat using -Q\n")
            self.assertTrue(self.m.native_sync_supported(home))
            self.assertTrue(self.m.is_ready(home))
            self.assertIn("no Hermes patch required", self.m.install(home))

    def test_old_layout_can_still_be_repaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            tools = home / "hermes-agent/tools"
            tools.mkdir(parents=True)
            target = tools / "delegate_tool.py"
            target.write_text(
                "import logging\n\n"
                "def delegate(background, is_truthy_value):\n"
                "    background = is_truthy_value(background, default=False) if background is not None else False\n\n"
                "    # Depth limit — configurable via delegation.max_spawn_depth,\n"
                "    return background\n"
            )
            result = self.m.install(home)
            self.assertIn("installed legacy compatibility hook", result)
            self.assertTrue(self.m.legacy_patch_installed(home))


if __name__ == "__main__":
    unittest.main()
