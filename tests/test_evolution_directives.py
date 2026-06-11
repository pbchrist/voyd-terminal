"""Hermetic test suite for the Voyd Terminal evolution pipeline.

No LLM calls, no network: qwen_chat is mocked wherever a code path would reach it.
Run with: python3 -m unittest discover -s tests -v
"""
import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]

ARCHETYPES = ("person_present", "person_gone", "self_regret", "self_unlived")

# Deterministic choice routing at the authored branch points (mirrors scripts/llm_play.py)
ARCHETYPE_ROUTING = {
    "1.0": {"person_present": 1, "person_gone": 1, "self_regret": 2, "self_unlived": 2},
    "3.0": {"person_present": 1, "person_gone": 1, "self_regret": 2, "self_unlived": 2},
    "4.1": {"person_present": 1, "person_gone": 2},
    "4.2": {"self_regret": 1, "self_unlived": 2},
}


def load_json(relative):
    return json.loads((ROOT / relative).read_text())


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def walk_act1(nodes, archetype):
    """Deterministically traverse Act 1 as the given archetype.

    Returns (path, detected_archetype, portal_value). Mirrors the frontend logic in
    frontend/index.html renderAct1Node(): choices apply deltas, open nodes follow
    next_archetype, ACT2 terminates the walk.
    """
    current, portal, detected, path = "1.0", 8, None, []
    for _ in range(100):
        node = nodes.get(current)
        if node is None:
            break
        path.append(current)
        label = node.get("label", "")
        if label.startswith("name_"):
            detected = label.replace("name_", "")
        if node.get("open"):
            nxt = node.get("next", "ACT2")
            archetype_map = node.get("next_archetype") or {}
            if detected and detected in archetype_map:
                nxt = archetype_map[detected]
        else:
            choices = node.get("choices", [])
            if not choices:
                break
            pick = ARCHETYPE_ROUTING.get(current, {}).get(archetype, 1)
            choice = choices[pick - 1]
            portal = max(0, min(100, portal + choice.get("delta", 0)))
            nxt = choice.get("next", "ACT2")
        if nxt == "ACT2" or nxt not in nodes:
            path.append("ACT2")
            break
        current = nxt
    return path, detected, portal


class GraphIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nodes = load_json("data/act1_nodes.json")["nodes"]
        cls.evolve = load_module("evolve", "evolve.py")

    def test_all_pointers_resolve(self):
        for node_id, node in self.nodes.items():
            direct = node.get("next")
            if direct:
                self.assertTrue(direct == "ACT2" or direct in self.nodes,
                                f"{node_id} has unresolved next {direct}")
            for archetype, target in (node.get("next_archetype") or {}).items():
                self.assertTrue(target == "ACT2" or target in self.nodes,
                                f"{node_id} next_archetype[{archetype}] unresolved: {target}")
            for choice in node.get("choices", []):
                nxt = choice.get("next")
                self.assertTrue(nxt == "ACT2" or nxt in self.nodes,
                                f"{node_id} choice '{choice.get('label')}' unresolved: {nxt}")

    def test_frontend_copy_in_sync(self):
        frontend = load_json("frontend/data/act1_nodes.json")
        self.assertEqual(load_json("data/act1_nodes.json"), frontend,
                         "frontend/data/act1_nodes.json out of sync — run build_frontend.py")

    def test_generated_nodes_reachable_and_interactive(self):
        reachable = self.evolve.reachable_nodes(self.nodes, "1.0")
        gen_ids = sorted(n for n in self.nodes if n.startswith("gen_"))
        self.assertTrue(gen_ids, "expected at least one generated node")
        for gen_id in gen_ids:
            self.assertIn(gen_id, reachable, f"{gen_id} is not reachable from 1.0")
            choices = self.nodes[gen_id].get("choices")
            self.assertTrue(choices, f"{gen_id} needs choices")
            self.assertEqual({c["type"] for c in choices}, {"feed", "starve"})

    def test_archetype_walks(self):
        for archetype in ARCHETYPES:
            path, detected, portal = walk_act1(self.nodes, archetype)
            self.assertEqual(detected, archetype, f"walk failed to set archetype {archetype}")
            self.assertIn("10.0", path)
            self.assertIn("gen_1", path, f"{archetype} walk never reaches gen_1")
            self.assertEqual(path[-1], "ACT2", f"{archetype} walk did not reach ACT2: {path}")
            self.assertTrue(0 <= portal <= 100)

    def test_choices_have_real_cost(self):
        # Every feed/starve pair must move the portal value in opposite directions.
        for node_id, node in self.nodes.items():
            choices = node.get("choices", [])
            types = {c.get("type") for c in choices}
            if types == {"feed", "starve"}:
                for c in choices:
                    if c["type"] == "feed":
                        self.assertGreater(c.get("delta", 0), 0,
                                           f"{node_id} feed choice has no positive delta")
                    else:
                        self.assertLess(c.get("delta", 0), 0,
                                        f"{node_id} starve choice has no negative delta")


class StoryMapConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.act_nodes = load_json("data/act1_nodes.json")["nodes"]
        cls.story = load_json("data/story_map.json")

    def test_story_map_targets_exist(self):
        story_nodes = self.story["nodes"]
        for node_id, meta in story_nodes.items():
            self.assertIn(node_id, self.act_nodes, f"story_map node {node_id} missing from act graph")
            for nxt in meta.get("branches_to", []):
                self.assertTrue(nxt == "ACT2" or nxt in story_nodes,
                                f"story_map {node_id} branches to missing {nxt}")

    def test_story_map_mirrors_act_graph_edges(self):
        story_nodes = self.story["nodes"]
        for node_id, meta in story_nodes.items():
            act_node = self.act_nodes[node_id]
            actual = []
            for target in (act_node.get("next_archetype") or {}).values():
                if target not in actual:
                    actual.append(target)
            if not actual:
                for choice in act_node.get("choices", []):
                    if choice["next"] not in actual:
                        actual.append(choice["next"])
                if not actual and act_node.get("next"):
                    actual.append(act_node["next"])
            self.assertEqual(sorted(meta.get("branches_to", [])), sorted(actual),
                             f"story_map {node_id} branches_to does not match the act graph")

    def test_no_raw_llm_transcripts_in_shipped_data(self):
        for node in self.act_nodes.values():
            score = node.get("score")
            if isinstance(score, dict):
                self.assertNotIn("raw", score, f"{node.get('id')} ships a raw LLM transcript")


class EvolvePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evolve = load_module("evolve", "evolve.py")

    def test_directive_pipeline_api(self):
        for name in [
            "load_state", "detect_structural_issues", "select_canon_event",
            "generate_node", "score_node", "promote_node", "record_decision",
            "send_uncertain_node_to_telegram", "send_structural_issues_to_telegram",
            "poll_telegram_for_reply", "recalibrate_rubric", "acquire_lock",
        ]:
            self.assertTrue(hasattr(self.evolve, name), f"missing {name}")

    def test_detect_structural_issues_clean(self):
        state = self.evolve.load_state(ROOT)
        self.assertEqual([], self.evolve.detect_structural_issues(state))

    def test_find_act2_frontier_includes_all_node_kinds(self):
        state = self.evolve.load_state(ROOT)
        frontier = self.evolve.find_act2_frontier(state["act1_nodes"]["nodes"])
        # gen_1 is the current frontier; the function must not filter by id prefix.
        self.assertEqual(frontier, ["gen_1"])

    def _rubric(self):
        return load_json("data/rubric.json")

    def _node(self):
        return {
            "label": "test", "text": "the stone remembered her circle. i did not.",
            "dialectic_role": "turn", "type": "beat", "act": 2, "tension_delta": 0.1,
            "canon_event": "portal_moves_overnight",
            "choices": [
                {"label": "a", "type": "feed", "delta": 3, "next": "ACT2"},
                {"label": "b", "type": "starve", "delta": -2, "next": "ACT2"},
            ],
        }

    def test_score_node_parses_axes_and_promotes(self):
        reply = ("DIALECTIC_FUNCTION: 9\nTENSION_ADVANCEMENT: 8\n"
                 "BRANCH_CHOKE_LOGIC: 8\nREASON: strong turn.")
        with mock.patch.object(self.evolve, "qwen_chat", return_value=reply):
            score = self.evolve.score_node(self._node(), self._rubric(), {"nodes": {}})
        self.assertEqual(score["axes"], {
            "dialectic_function": 9, "tension_advancement": 8, "branch_choke_logic": 8,
        })
        self.assertEqual(score["total"], 25)
        self.assertEqual(score["decision"], "promote")
        self.assertEqual(score["reason"], "strong turn.")

    def test_score_node_uncertain_and_kill_zones(self):
        cases = [(("6", "6", "6"), "uncertain"), (("4", "4", "4"), "kill"), (("8", "8", "8"), "promote")]
        for (a, b, c), expected in cases:
            reply = (f"DIALECTIC_FUNCTION: {a}\nTENSION_ADVANCEMENT: {b}\n"
                     f"BRANCH_CHOKE_LOGIC: {c}\nREASON: x")
            with mock.patch.object(self.evolve, "qwen_chat", return_value=reply):
                score = self.evolve.score_node(self._node(), self._rubric(), {"nodes": {}})
            self.assertEqual(score["decision"], expected, f"axes {(a, b, c)}")

    def test_score_node_llm_failure_is_uncertain(self):
        with mock.patch.object(self.evolve, "qwen_chat", side_effect=OSError("down")):
            score = self.evolve.score_node(self._node(), self._rubric(), {"nodes": {}})
        self.assertEqual(score["decision"], "uncertain")
        self.assertEqual(score["total"], 18)

    def test_promote_node_rewires_real_frontier(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(ROOT / "data", tmp_root / "data")
            state = self.evolve.load_state(tmp_root)
            node = self._node()
            score = {"axes": {a: 9 for a in self.evolve.SCORE_AXES}, "total": 27,
                     "reason": "x", "decision": "promote", "raw": "transcript"}
            new_id = self.evolve.promote_node(state, node, score, tmp_root)

            act = json.loads((tmp_root / "data/act1_nodes.json").read_text())
            nodes = act["nodes"]
            self.assertIn(new_id, nodes)
            # The old frontier (gen_1) must now point at the new node, not ACT2.
            for choice in nodes["gen_1"]["choices"]:
                self.assertEqual(choice["next"], new_id)
            # The new node carries no raw transcript.
            self.assertNotIn("raw", nodes[new_id]["score"])

            story = json.loads((tmp_root / "data/story_map.json").read_text())
            self.assertIn(new_id, story["nodes"])
            self.assertEqual(story["nodes"]["gen_1"]["branches_to"], [new_id])
            self.assertEqual(story["nodes"][new_id]["converges_from"], ["gen_1"])
            self.assertEqual(story["open_branches"], ["ACT2"])

            events = json.loads((tmp_root / "data/canon_events.json").read_text())
            used = next(e for e in events if e["id"] == "portal_moves_overnight")
            self.assertTrue(used["used"])
            self.assertEqual(used["node_id"], new_id)


class RecalibrateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evolve = load_module("evolve_recal", "evolve.py")

    def _rubric(self, decisions):
        return {
            "axes": {
                "dialectic_function": {"weight": 0.4, "threshold": 7},
                "tension_advancement": {"weight": 0.35, "threshold": 6},
                "branch_choke_logic": {"weight": 0.25, "threshold": 6},
            },
            "auto_promote_threshold": 24,
            "auto_kill_threshold": 18,
            "decisions": decisions,
        }

    def test_recalibrate_adjusts_weights(self):
        decisions = [{"score": {"axes": {a: 10 for a in self.evolve.SCORE_AXES}}} for _ in range(5)]
        rubric = self._rubric(decisions)
        self.evolve.recalibrate_rubric(rubric)
        self.assertIsNotNone(rubric.get("last_recalibrated"))
        weights = {a: rubric["axes"][a]["weight"] for a in self.evolve.SCORE_AXES}
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=1)

    def test_recalibrate_tolerates_legacy_decision_formats(self):
        # Old dramaturg-format entries (no axes) must be skipped, not crash.
        decisions = [{"score": {"score": 9, "reason": "legacy"}}] * 3 + [
            {"score": {"axes": {a: 9 for a in self.evolve.SCORE_AXES}}} for _ in range(4)
        ]
        rubric = self._rubric(decisions)
        self.evolve.recalibrate_rubric(rubric)  # only 4 axis-scored: below minimum, no-op
        self.assertIsNone(rubric.get("last_recalibrated"))
        decisions.append({"score": {"axes": {a: 9 for a in self.evolve.SCORE_AXES}}})
        self.evolve.recalibrate_rubric(rubric)
        self.assertIsNotNone(rubric.get("last_recalibrated"))

    def test_record_decision_recalibrates_every_five(self):
        rubric = self._rubric([{"score": {"axes": {a: 10 for a in self.evolve.SCORE_AXES}}}] * 4)
        self.evolve.record_decision(rubric, {"score": {"axes": {a: 10 for a in self.evolve.SCORE_AXES}}})
        self.assertIsNotNone(rubric.get("last_recalibrated"))


class PhantomWalkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pw = load_module("phantom_walkers", "scripts/phantom_walkers.py")

    def test_jaccard(self):
        self.assertEqual(self.pw.jaccard_similarity({1, 2}, {1, 2}), 1.0)
        self.assertEqual(self.pw.jaccard_similarity({1}, {2}), 0.0)

    def test_min_uniqueness_ignores_shared_candidate_when_excluded(self):
        base = [["1.0", "a", "x"], ["1.0", "b", "y"], ["1.0", "c", "z"], ["1.0", "d", "w"]]
        baseline = self.pw.min_uniqueness(base)
        with_candidate = [p + ["cand"] for p in base]
        stripped = [[n for n in p if n != "cand"] for p in with_candidate]
        self.assertEqual(self.pw.min_uniqueness(stripped), baseline)
        # And counting the shared candidate would have lowered uniqueness:
        self.assertLess(self.pw.min_uniqueness(with_candidate), baseline)


if __name__ == "__main__":
    unittest.main()
