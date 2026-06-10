import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_json(relative):
    return json.loads((ROOT / relative).read_text())


def load_evolve_module():
    spec = importlib.util.spec_from_file_location("evolve", ROOT / "evolve.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EvolutionDirectiveTests(unittest.TestCase):
    def test_generated_nodes_are_reachable_after_10_with_choices(self):
        data = load_json("data/act1_nodes.json")
        nodes = data["nodes"]

        self.assertEqual(nodes["10.0"].get("next"), "gen_1")

        reachable = set()
        stack = ["10.0"]
        while stack:
            node_id = stack.pop()
            if node_id in reachable or node_id == "ACT2":
                continue
            reachable.add(node_id)
            node = nodes[node_id]
            for choice in node.get("choices", []):
                nxt = choice.get("next")
                self.assertTrue(nxt == "ACT2" or nxt in nodes, f"{node_id} has unresolved next {nxt}")
                stack.append(nxt)
            direct = node.get("next")
            if direct:
                self.assertTrue(direct == "ACT2" or direct in nodes, f"{node_id} has unresolved next {direct}")
                stack.append(direct)

        for i in range(1, 13):
            gen_id = f"gen_{i}"
            self.assertIn(gen_id, reachable)
            choices = nodes[gen_id].get("choices")
            self.assertIsInstance(choices, list, f"{gen_id} needs choices")
            self.assertTrue(choices, f"{gen_id} needs choices")
            self.assertEqual({c["type"] for c in choices}, {"feed", "starve"})

    def test_evolve_module_implements_directive_pipeline_api(self):
        evolve = load_evolve_module()
        for name in [
            "load_state",
            "detect_structural_issues",
            "select_canon_event",
            "generate_node",
            "score_node",
            "promote_node",
            "send_uncertain_node_to_telegram",
            "send_structural_issues_to_telegram",
            "poll_telegram_for_reply",
            "recalibrate_rubric",
        ]:
            self.assertTrue(hasattr(evolve, name), f"missing {name}")

        state = evolve.load_state(ROOT)
        self.assertIn("story_map", state)
        self.assertIn("rubric", state)
        self.assertIn("canon_events", state)

        # Select an unused canon event
        portal_event = next(
            (event for event in state["canon_events"] if event["id"] == "portal_moves_overnight"),
            None,
        )
        if portal_event and not portal_event.get("used"):
            event = evolve.select_canon_event(state, preferred_id="portal_moves_overnight")
        else:
            event = evolve.select_canon_event(state)

        self.assertIn("voyd_pov", event)

        node = evolve.generate_node(state, event)
        self.assertEqual(node["canon_event"], event["id"])
        self.assertEqual(node["text"], node["text"].lower())
        # Text should incorporate the seed's core image, not the generic fallback suffix
        self.assertNotIn("i gave back the part that could be used", node["text"])
        self.assertEqual(len(node["choices"]), 2)
        self.assertEqual({choice["type"] for choice in node["choices"]}, {"feed", "starve"})

        score = evolve.score_node(node, state["rubric"], state["story_map"])
        self.assertEqual(set(score["axes"]), {
            "dialectic_function",
            "tension_advancement",
            "branch_choke_logic",
        })
        self.assertGreaterEqual(score["total"], 18)
        self.assertIn(score["decision"], {"promote", "kill", "uncertain"})

    def test_score_node_is_event_agnostic(self):
        evolve = load_evolve_module()
        story_map = {"act": 2, "dialectic_position": "antithesis_peak"}
        rubric = {
            "axes": {
                "dialectic_function": {"weight": 0.4, "threshold": 7},
                "tension_advancement": {"weight": 0.35, "threshold": 6},
                "branch_choke_logic": {"weight": 0.25, "threshold": 6},
            },
            "auto_promote_threshold": 24,
            "auto_kill_threshold": 18,
        }

        # Node with portal-specific words
        node_portal = {
            "text": "she put me where she wanted me. in the morning i was where i wanted to be. the stone remembered her circle. i did not. i had learned the shape of preference.",
            "dialectic_role": "antithesis_peak",
            "act": 2,
            "canon_event": "portal_moves_overnight",
            "tension_delta": 0.15,
            "choices": [
                {"type": "feed", "next": "ACT2"},
                {"type": "starve", "next": "ACT2"},
            ],
        }

        # Node without portal-specific words but with other intense words
        node_other = {
            "text": "the grief opened like a wound. fear held the silence. loss pulled at every thread until the fabric tore.",
            "dialectic_role": "antithesis_peak",
            "act": 2,
            "canon_event": "sol_wife_returns",
            "tension_delta": 0.15,
            "choices": [
                {"type": "feed", "next": "ACT2"},
                {"type": "starve", "next": "ACT2"},
            ],
        }

        score_portal = evolve.score_node(node_portal, rubric, story_map)
        score_other = evolve.score_node(node_other, rubric, story_map)
        self.assertGreaterEqual(score_other["axes"]["tension_advancement"], 8)
        self.assertAlmostEqual(
            score_portal["axes"]["tension_advancement"],
            score_other["axes"]["tension_advancement"],
            delta=2,
            msg="tension_advancement should not be heavily biased toward portal_moves_overnight words",
        )

    def test_recalibrate_rubric_adjusts_weights(self):
        evolve = load_evolve_module()
        rubric = {
            "axes": {
                "dialectic_function": {"weight": 0.4, "threshold": 7},
                "tension_advancement": {"weight": 0.35, "threshold": 6},
                "branch_choke_logic": {"weight": 0.25, "threshold": 6},
            },
            "auto_promote_threshold": 24,
            "auto_kill_threshold": 18,
            "decisions": [
                {"score": {"axes": {"dialectic_function": 10, "tension_advancement": 10, "branch_choke_logic": 10}}},
                {"score": {"axes": {"dialectic_function": 10, "tension_advancement": 10, "branch_choke_logic": 10}}},
                {"score": {"axes": {"dialectic_function": 10, "tension_advancement": 10, "branch_choke_logic": 10}}},
                {"score": {"axes": {"dialectic_function": 10, "tension_advancement": 10, "branch_choke_logic": 10}}},
                {"score": {"axes": {"dialectic_function": 10, "tension_advancement": 10, "branch_choke_logic": 10}}},
            ],
        }
        evolve.recalibrate_rubric(rubric)
        self.assertIsNotNone(rubric.get("last_recalibrated"))
        self.assertIn("pending_weight_suggestion", rubric)
        weights = {
            k: rubric["axes"][k]["weight"]
            for k in ("dialectic_function", "tension_advancement", "branch_choke_logic")
        }
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=1)
        # All axes scored far above threshold, so weights should drift from baseline
        self.assertNotEqual(
            weights,
            {"dialectic_function": 0.4, "tension_advancement": 0.35, "branch_choke_logic": 0.25},
            msg="weights should change when all axes consistently score far above threshold",
        )


if __name__ == "__main__":
    unittest.main()
