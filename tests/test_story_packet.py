"""Deterministic authoritative play-packet tests."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = {"demanded_identity", "claimed_knowledge", "demanded_motive", "identity_as_bait"}


def load_builder():
    spec = importlib.util.spec_from_file_location("build_story_packet", ROOT / "scripts/build_story_packet.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StoryPacketTests(unittest.TestCase):
    def test_packet_covers_thresholds_and_complete_live_bargain(self):
        packet = load_builder().build_packet()
        self.assertEqual(packet["selected_structural_species"],
                         "mutation_revelation_threshold_then_live_bargain")
        walks = packet["walks"]
        self.assertEqual({w["route"] for w in walks}, ROUTES)
        for route in ROUTES:
            variants = {w["resolution_variant"]: w for w in walks if w["route"] == route}
            self.assertEqual(set(variants), {"withdraw", "pending", "declined", "reframe_required",
                                             "accepted", "refused", "fulfilled", "breached"})
            closed = variants["withdraw"]["handoff"]
            self.assertEqual(closed["lifecycle"], "unbound_closed")
            self.assertTrue(closed["revelation_text"])
            self.assertIsNone(closed["contract_identity"])
            self.assertIsNone(closed["unpaid_cost"])
            self.assertNotIn("contract", variants["withdraw"]["act2_opening"].lower())

            pending = variants["pending"]["handoff"]
            self.assertEqual(pending["lifecycle"], "petition_pending")
            self.assertEqual(pending["threshold_election"], "seek_change")
            self.assertIsNone(pending["petition_text"])
            self.assertIsNone(pending["contract_identity"])
            self.assertEqual(pending["terms"], [])
            self.assertIsNone(pending["unpaid_cost"])

            for no_contract in ("declined", "reframe_required"):
                state = variants[no_contract]["handoff"]
                self.assertIsNone(state["contract_identity"])
                self.assertEqual(state["terms"], [])
                self.assertIsNone(state["unpaid_cost"])

            for outcome in ("accepted", "refused"):
                state = variants[outcome]["handoff"]
                self.assertTrue(state["petition_text"])
                self.assertTrue(state["counterforce_id"])
                self.assertTrue(state["counterforce_text"])
                self.assertTrue(state["terms"])
                self.assertIn(state["terms_constraint"], variants[outcome]["act2_prompt"])
            self.assertTrue(variants["accepted"]["handoff"]["contract_identity"])
            self.assertIsNone(variants["refused"]["handoff"]["contract_identity"])
            self.assertTrue(variants["accepted"]["handoff"]["unpaid_cost"])
            self.assertIsNone(variants["refused"]["handoff"]["unpaid_cost"])
            fulfilled = variants["fulfilled"]["handoff"]
            breached = variants["breached"]["handoff"]
            self.assertEqual(fulfilled["lifecycle"], "fulfilled")
            self.assertIsNone(fulfilled["unpaid_cost"])
            self.assertEqual(breached["lifecycle"], "breached")
            self.assertTrue(breached["breach_consequence"])
            self.assertEqual(breached["unpaid_cost"], breached["breach_consequence"])

        cases = packet["adversarial_classifier_cases"]
        self.assertEqual(len(cases), 16)
        expected = {
            "nothing": "petition_declined",
            "take me back and retrieve the person i lost": "petition_reframe_required",
            "keep my present promise with my friend": "petition_validated",
            "go back forty years": "petition_reframe_required",
        }
        for case in cases:
            self.assertEqual(case["expected_lifecycle"], expected[case["input"]])
            self.assertEqual(case["handoff"]["lifecycle"], case["expected_lifecycle"])
            self.assertIsNone(case["handoff"]["contract_identity"])
            self.assertEqual(case["handoff"]["terms"], [])
            self.assertIsNone(case["handoff"]["unpaid_cost"])

    def test_packet_serializes_without_model_calls(self):
        packet = load_builder().build_packet()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "packet.json"
            path.write_text(json.dumps(packet), encoding="utf-8")
            loaded = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(loaded["schema_version"], 2)
        self.assertEqual(len(loaded["walks"]), 32)


if __name__ == "__main__":
    unittest.main()
