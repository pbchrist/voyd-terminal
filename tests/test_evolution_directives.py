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
        ]:
            self.assertTrue(hasattr(evolve, name), f"missing {name}")

        state = evolve.load_state(ROOT)
        self.assertIn("story_map", state)
        self.assertIn("rubric", state)
        self.assertIn("canon_events", state)
        portal_event = next(event for event in state["canon_events"] if event["id"] == "portal_moves_overnight")
        event = portal_event if portal_event.get("used") else evolve.select_canon_event(state, preferred_id="portal_moves_overnight")
        self.assertEqual(event["id"], "portal_moves_overnight")

        node = evolve.generate_node(state, event)
        self.assertEqual(node["canon_event"], "portal_moves_overnight")
        self.assertEqual(node["text"], node["text"].lower())
        self.assertIn("she put me where she wanted me", node["text"])
        self.assertEqual(len(node["choices"]), 2)
        self.assertEqual({choice["type"] for choice in node["choices"]}, {"feed", "starve"})

        score = evolve.score_node(node, state["rubric"], state["story_map"])
        self.assertEqual(set(score["axes"]), {
            "dialectic_function",
            "tension_advancement",
            "branch_choke_logic",
        })
        self.assertGreaterEqual(score["total"], 24)


if __name__ == "__main__":
    unittest.main()
