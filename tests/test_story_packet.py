"""Deterministic authoritative play-packet tests."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location("build_story_packet", ROOT / "scripts" / "build_story_packet.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StoryPacketTests(unittest.TestCase):
    def test_packet_covers_all_contracts_and_counter_resolutions(self):
        builder = load_builder()
        packet = builder.build_packet()
        walks = packet["walks"]
        self.assertEqual(len(walks), 8)
        by_route = {}
        for walk in walks:
            by_route.setdefault(walk["route"], []).append(walk)
            self.assertEqual(walk["route"], walk["contract"]["identity"])
            self.assertTrue(walk["path"])
            self.assertTrue(walk["act2_opening"])
            self.assertIn(walk["route"], walk["act2_prompt"])
        self.assertEqual(set(by_route), set(builder.ROUTES))
        for route, variants in by_route.items():
            self.assertEqual(len(variants), 2, route)
            self.assertEqual({v["resolution_variant"] for v in variants}, {"primary_resolution", "counter_resolution"})
            self.assertEqual(len({v["contract"]["resolution"] for v in variants}), 2, route)

    def test_packet_serializes_without_model_calls(self):
        builder = load_builder()
        packet = builder.build_packet()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "packet.json"
            path.write_text(json.dumps(packet), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema_version"], 1)
        self.assertEqual(len(loaded["walks"]), 8)


if __name__ == "__main__":
    unittest.main()
