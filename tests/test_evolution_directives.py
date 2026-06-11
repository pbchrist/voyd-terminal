"""Hermetic test suite for the Voyd Terminal evolution pipeline.

No LLM calls, no network: qwen_chat is mocked wherever a code path would reach it.
Run with: python3 -m unittest discover -s tests -v
"""
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

os.environ["VOYD_TEST"] = "1"  # keep test runs out of logs/evolve.log

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
        # The frontier moves every time the organism grows, so assert structure, not ids:
        # exactly the nodes with a choice into ACT2, and never empty.
        state = self.evolve.load_state(ROOT)
        nodes = state["act1_nodes"]["nodes"]
        frontier = self.evolve.find_act2_frontier(nodes)
        expected = sorted(
            nid for nid, node in nodes.items()
            if any(c.get("next") == "ACT2" for c in node.get("choices", []))
        )
        self.assertEqual(sorted(frontier), expected)
        self.assertTrue(frontier)

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
                 "BRANCH_CHOKE_LOGIC: 8\n"
                 "PRECEDENT: the bargain in Faust; it earns the comparison.\n"
                 "REASON: strong turn.")
        with mock.patch.object(self.evolve, "qwen_chat", return_value=reply):
            score = self.evolve.score_node(self._node(), self._rubric(), {"nodes": {}})
        self.assertEqual(score["axes"], {
            "dialectic_function": 9, "tension_advancement": 8, "branch_choke_logic": 8,
        })
        self.assertEqual(score["total"], 25)
        self.assertEqual(score["decision"], "promote")
        self.assertEqual(score["reason"], "strong turn.")
        self.assertIn("Faust", score["precedent"])

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
            old_frontier = self.evolve.find_act2_frontier(state["act1_nodes"]["nodes"])
            node = self._node()
            score = {"axes": {a: 9 for a in self.evolve.SCORE_AXES}, "total": 27,
                     "reason": "x", "decision": "promote", "raw": "transcript"}
            new_id = self.evolve.promote_node(state, node, score, tmp_root)

            act = json.loads((tmp_root / "data/act1_nodes.json").read_text())
            nodes = act["nodes"]
            self.assertIn(new_id, nodes)
            # Every old frontier node must now point at the new node, not ACT2.
            for fid in old_frontier:
                for choice in nodes[fid]["choices"]:
                    self.assertEqual(choice["next"], new_id)
            # The new node carries no raw transcript.
            self.assertNotIn("raw", nodes[new_id]["score"])

            story = json.loads((tmp_root / "data/story_map.json").read_text())
            self.assertIn(new_id, story["nodes"])
            for fid in old_frontier:
                self.assertEqual(story["nodes"][fid]["branches_to"], [new_id])
            self.assertEqual(sorted(story["nodes"][new_id]["converges_from"]),
                             sorted(old_frontier))
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

    def test_find_kills_spares_terminal_convergence(self):
        # A gen node at the very end of every walk is convergence by design, not collapse.
        walks = [{"path": ["1.0", letter, "10.0", "gen_1"]} for letter in "abcd"]
        self.assertEqual(self.pw.find_kills(walks), [])

    def test_find_kills_flags_long_identical_gen_tail(self):
        walks = [{"path": ["1.0", letter, "gen_1", "gen_2", "gen_3"]} for letter in "abcd"]
        self.assertEqual(self.pw.find_kills(walks), ["gen_1"])

    def test_find_kills_never_flags_authored_nodes(self):
        walks = [{"path": ["1.0", letter, "9.0", "9.5", "9.9"]} for letter in "abcd"]
        self.assertEqual(self.pw.find_kills(walks), [])

    def test_score_experience_parses_judge_reply(self):
        walk = {
            "path": ["1.0", "2.1"],
            "node_texts": ["you have been here before.", "loss leaves a shape."],
            "choices_made": [{"node": "1.0", "label": "something i lost"}],
            "act2_response": "the shape you carry fits my mouth.",
        }
        reply = "SCORE: 7\nWEAKEST: 2.1\nREASON: the second beat restates the first."
        with mock.patch.object(self.pw, "qwen_chat", return_value=reply):
            result = self.pw.score_experience(walk)
        self.assertEqual(result["score"], 7)
        self.assertEqual(result["weakest"], "2.1")
        self.assertIn("restates", result["reason"])

    def test_walk_history_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            history = Path(tmp) / "walk_history.jsonl"
            with mock.patch.object(self.pw, "WALK_HISTORY_PATH", history):
                self.assertEqual(self.pw.walk_history_count(), 0)
                report = {"last_run": "now", "walks": [{"archetype": "a"}, {"archetype": "b"}]}
                with mock.patch.object(self.pw, "WALK_SCORES_PATH", Path(tmp) / "ws.json"):
                    self.pw.record_run(report)
                self.assertEqual(self.pw.walk_history_count(), 2)

    def test_build_report_message_quotes_beats(self):
        report = {
            "last_run": "2026-06-11T03:01:46",
            "walks": [
                {"archetype": "person_present", "scores": {"path_uniqueness": 6.67},
                 "experience": {"score": 8}},
                {"archetype": "self_regret", "scores": {"path_uniqueness": 7.0},
                 "experience": {"score": 7}},
            ],
            "kills_recommended": ["gen_9"],
            "reader_notes": [
                {"archetype": "person_present", "weakest": "gen_1",
                 "reason": "the color metaphors break the intimacy."},
                {"archetype": "self_regret", "weakest": "gen_1",
                 "reason": "abstract imagery stalls the momentum."},
            ],
        }
        nodes = {"gen_1": {"text": "four small lights pressing\n\nagainst me."}}
        msg = self.pw.build_report_message(report, nodes=nodes, cycle_summary="🌱 grew gen_2")
        self.assertIn("🌱 grew gen_2", msg)
        self.assertIn("person_present 8/10", msg)
        # The weakest beat is quoted (newlines flattened), grouped across readers, full reasons shown
        self.assertIn("four small lights pressing against me.", msg)
        self.assertIn("gen_1 — flagged by 2/2 readers", msg)
        self.assertIn("break the intimacy", msg)
        self.assertIn("stalls the momentum", msg)
        self.assertIn("gen_9", msg)
        self.assertLessEqual(len(msg), 4000)

    def test_build_report_message_truncates_for_telegram(self):
        report = {
            "last_run": "2026-06-11T03:01:46",
            "walks": [{"archetype": f"a{i}", "scores": {"path_uniqueness": 7.0},
                       "experience": {"score": 8}} for i in range(4)],
            "kills_recommended": [],
            "reader_notes": [
                {"archetype": f"a{i}", "weakest": f"n{i}", "reason": "x" * 400}
                for i in range(40)
            ],
        }
        msg = self.pw.build_report_message(report, nodes={})
        self.assertLessEqual(len(msg), 4001)


class RewriteNodeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rn = load_module("rewrite_node", "scripts/rewrite_node.py")

    def test_rewrite_replaces_prose_but_preserves_graph(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(ROOT / "data", tmp_root / "data")
            ev = self.rn.evolve
            gen_reply = json.dumps({
                "text": "the lights are her four names. each one a question she never asked aloud.",
                "choices": [
                    {"label": "answer for her", "type": "feed", "delta": 3},
                    {"label": "let the names starve", "type": "starve", "delta": -2},
                ],
            })
            judge_reply = ("DIALECTIC_FUNCTION: 9\nTENSION_ADVANCEMENT: 8\n"
                           "BRANCH_CHOKE_LOGIC: 8\nPRECEDENT: x\nREASON: better.")
            before = json.loads((tmp_root / "data/act1_nodes.json").read_text())["nodes"]["gen_1"]
            with mock.patch.object(self.rn, "REPO_ROOT", tmp_root), \
                 mock.patch.object(ev, "ACT1_NODES_PATH", tmp_root / "data/act1_nodes.json"), \
                 mock.patch.object(ev, "RUBRIC_PATH", tmp_root / "data/rubric.json"), \
                 mock.patch.object(ev, "qwen_chat", side_effect=[gen_reply, judge_reply]), \
                 mock.patch.object(ev, "run_build") as build, \
                 mock.patch.object(ev, "send_telegram_text", return_value=True):
                self.assertTrue(self.rn.rewrite("gen_1", max_attempts=1))
            after = json.loads((tmp_root / "data/act1_nodes.json").read_text())["nodes"]["gen_1"]
            self.assertNotEqual(after["text"], before["text"])
            # The graph is untouched: same id, same choice targets per type.
            self.assertEqual({c["type"]: c["next"] for c in after["choices"]},
                             {c["type"]: c["next"] for c in before["choices"]})
            self.assertEqual(after["score"]["total"], 25)
            self.assertNotIn("raw", after["score"])
            self.assertIn("rewritten_at", after)
            build.assert_called_once()
            rubric = json.loads((tmp_root / "data/rubric.json").read_text())
            self.assertEqual(rubric["decisions"][-1]["decision"], "rewrite")

    def test_rewrite_leaves_node_alone_when_dramaturg_unconvinced(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(ROOT / "data", tmp_root / "data")
            ev = self.rn.evolve
            gen_reply = json.dumps({
                "text": "x.",
                "choices": [
                    {"label": "a", "type": "feed", "delta": 3},
                    {"label": "b", "type": "starve", "delta": -2},
                ],
            })
            judge_reply = ("DIALECTIC_FUNCTION: 4\nTENSION_ADVANCEMENT: 4\n"
                           "BRANCH_CHOKE_LOGIC: 4\nREASON: worse.")
            before = json.loads((tmp_root / "data/act1_nodes.json").read_text())["nodes"]["gen_1"]
            with mock.patch.object(self.rn, "REPO_ROOT", tmp_root), \
                 mock.patch.object(ev, "ACT1_NODES_PATH", tmp_root / "data/act1_nodes.json"), \
                 mock.patch.object(ev, "RUBRIC_PATH", tmp_root / "data/rubric.json"), \
                 mock.patch.object(ev, "qwen_chat", side_effect=[gen_reply, judge_reply] * 2), \
                 mock.patch.object(ev, "run_build") as build, \
                 mock.patch.object(ev, "send_telegram_text", return_value=True):
                self.assertFalse(self.rn.rewrite("gen_1", max_attempts=2))
            after = json.loads((tmp_root / "data/act1_nodes.json").read_text())["nodes"]["gen_1"]
            self.assertEqual(after, before)
            build.assert_not_called()


class MinerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.miner = load_module("mine_canon", "scripts/mine_canon.py")

    def test_normalize_candidate(self):
        raw = {
            "id": "Sol's Wife!", "event": "Sol's wife comes home and does not recognize him at all.",
            "voyd_pov": "He Looked At Her Face — and understood.",
            "act": "3", "dialectic_role": "nonsense", "tension_level": "1.7",
        }
        cand = self.miner.normalize_candidate(raw, "Book 1", set())
        self.assertEqual(cand["id"], "sol_s_wife")
        self.assertEqual(cand["act"], 3)
        self.assertEqual(cand["dialectic_role"], "antithesis_deepening")
        self.assertEqual(cand["tension_level"], 1.0)
        self.assertNotIn("—", cand["voyd_pov"])
        self.assertEqual(cand["voyd_pov"], cand["voyd_pov"].lower())
        self.assertFalse(cand["used"])
        self.assertTrue(cand["mined"])

    def test_normalize_rejects_thin_candidates(self):
        self.assertIsNone(self.miner.normalize_candidate(
            {"event": "short", "voyd_pov": "tiny"}, "Book 1", set()))

    def test_is_duplicate_catches_near_copies(self):
        existing = [{"id": "sol_wife_returns",
                     "event": "Sol's wife comes home and does not recognize him. "
                              "He changed the timeline. He did not change himself."}]
        near_copy = {"id": "wife_return",
                     "event": "Sol's wife comes home and does not recognize him anymore. "
                              "He changed the timeline but he did not change himself."}
        fresh = {"id": "molten_spindle",
                 "event": "The astrolabe returns from the portal as a molten spindle "
                          "that bores through solid rock on contact."}
        self.assertTrue(self.miner.is_duplicate(near_copy, existing))
        self.assertFalse(self.miner.is_duplicate(fresh, existing))

    def test_mine_end_to_end_with_mocked_llm(self):
        candidate_json = json.dumps([{
            "id": "ash_rain_choir",
            "event": "After the portal doubles again, ash falls over the camp for a full day "
                     "and the Adherents sing into it, calling the ash a blessing.",
            "voyd_pov": "they sang into the falling grey. i let them believe it was weather.",
            "act": 2, "dialectic_role": "antithesis_deepening", "tension_level": 0.6,
        }])

        def fake_qwen(messages, max_tokens=300, temperature=0.7):
            prompt = messages[0]["content"]
            if "Return ONLY a JSON array" in prompt:
                return candidate_json
            return "SCORE: 8\nREASON: charged and canon-faithful."

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / "data").mkdir()
            shutil.copy(ROOT / "data/canon_events.json", tmp_root / "data/canon_events.json")
            book = tmp_root / "book.txt"
            book.write_text("a segment of book text " * 50)
            with mock.patch.object(self.miner, "qwen_chat", side_effect=fake_qwen), \
                 mock.patch.object(self.miner, "BOOK_SOURCES", [("Book T", book)]), \
                 mock.patch.object(self.miner, "MINE_STATE_PATH", tmp_root / "data/mine_state.json"):
                accepted = self.miner.mine(max_accept=1, max_segments=2, root=tmp_root)

            self.assertEqual(len(accepted), 1)
            self.assertEqual(accepted[0]["id"], "ash_rain_choir")
            self.assertEqual(accepted[0]["mine_score"], 8)
            events = json.loads((tmp_root / "data/canon_events.json").read_text())
            self.assertIn("ash_rain_choir", {e["id"] for e in events})
            # Cursor state persisted for the rotating scan
            self.assertTrue((tmp_root / "data/mine_state.json").exists())

    def test_mine_rejects_below_threshold(self):
        candidate_json = json.dumps([{
            "id": "mundane_moment",
            "event": "Two cats share breakfast near the camp and discuss the unusually warm weather.",
            "voyd_pov": "they ate. i waited. nothing about the morning belonged to me yet.",
            "act": 2, "dialectic_role": "antithesis_deepening", "tension_level": 0.2,
        }])

        def fake_qwen(messages, max_tokens=300, temperature=0.7):
            prompt = messages[0]["content"]
            if "Return ONLY a JSON array" in prompt:
                return candidate_json
            return "SCORE: 4\nREASON: mundane."

        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            (tmp_root / "data").mkdir()
            shutil.copy(ROOT / "data/canon_events.json", tmp_root / "data/canon_events.json")
            book = tmp_root / "book.txt"
            book.write_text("a segment of book text " * 50)
            before = json.loads((tmp_root / "data/canon_events.json").read_text())
            with mock.patch.object(self.miner, "qwen_chat", side_effect=fake_qwen), \
                 mock.patch.object(self.miner, "BOOK_SOURCES", [("Book T", book)]), \
                 mock.patch.object(self.miner, "MINE_STATE_PATH", tmp_root / "data/mine_state.json"):
                accepted = self.miner.mine(max_accept=1, max_segments=2, root=tmp_root)
            self.assertEqual(accepted, [])
            after = json.loads((tmp_root / "data/canon_events.json").read_text())
            self.assertEqual(len(before), len(after))


class ImmuneSystemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evolve = load_module("evolve_immune", "evolve.py")

    def test_dormant_below_walk_gate(self):
        # With a fresh (empty) history the immune system must refuse to operate.
        pw_stub = mock.Mock()
        pw_stub.walk_history_count.return_value = 3
        with mock.patch.object(self.evolve, "_load_script", return_value=pw_stub):
            active, count = self.evolve.immune_active()
        self.assertFalse(active)
        self.assertEqual(count, 3)

    def test_heal_returns_all_issues_when_dormant(self):
        pw_stub = mock.Mock()
        pw_stub.walk_history_count.return_value = 0
        with mock.patch.object(self.evolve, "_load_script", return_value=pw_stub):
            healed, remaining = self.evolve.heal_structural_issues(
                {"story_map": {}, "canon_events": [], "act1_nodes": {"nodes": {}}, "rubric": {}},
                ["some issue"], [("4.1", "gen_9")])
        self.assertEqual(healed, [])
        self.assertEqual(len(remaining), 2)

    def test_active_at_walk_gate(self):
        pw_stub = mock.Mock()
        pw_stub.walk_history_count.return_value = self.evolve.IMMUNE_WALK_GATE
        with mock.patch.object(self.evolve, "_load_script", return_value=pw_stub):
            active, _ = self.evolve.immune_active()
        self.assertTrue(active)

    def test_detect_stranded_chokes_only_checks_gen_chokes(self):
        story = {"nodes": {
            "4.1": {"type": "branch", "branches_to": ["5.1"]},
            "5.1": {"type": "beat", "branches_to": ["9.1p"]},
            "9.1p": {"type": "choke", "branches_to": ["10.0"]},   # authored: exempt
            "4.2": {"type": "branch", "branches_to": ["5.3"]},
            "5.3": {"type": "beat", "branches_to": ["gen_9"]},
            "gen_9": {"type": "choke", "branches_to": ["ACT2"]},  # generated: must catch all
        }}
        stranded = self.evolve.detect_stranded_chokes(story)
        self.assertEqual(stranded, [("4.1", "gen_9")])

    def test_external_patterns_and_reader_feedback_parsing(self):
        rubric = {"external_analysis": [{"findings": [
            {"analysis": {"patterns": ["early branch, late choke", "tension stair-step"]}},
        ]}]}
        patterns = self.evolve.external_patterns(rubric)
        self.assertEqual(len(patterns), 2)
        self.assertEqual(self.evolve.external_patterns({}), [])


class CommitDataChangesTests(unittest.TestCase):
    """The organism commits its cycle data on feat branches, never on main."""

    @classmethod
    def setUpClass(cls):
        cls.evolve = load_module("evolve", "evolve.py")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.origin = self.tmp / "origin.git"
        self.repo = self.tmp / "repo"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.repo)],
                       check=True, capture_output=True)
        self.git("config", "user.email", "test@test")
        self.git("config", "user.name", "test")
        (self.repo / "data").mkdir()
        (self.repo / "frontend").mkdir()
        (self.repo / "data" / "act1_nodes.json").write_text("{}")
        (self.repo / "frontend" / "voyd_data.json").write_text("{}")
        (self.repo / "evolve.py").write_text("# code")
        self.git("add", "-A")
        self.git("commit", "-qm", "init")
        self.git("push", "-q", "-u", "origin", "main")

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              capture_output=True, text=True)

    def test_commits_and_pushes_data_on_feat_branch(self):
        self.git("checkout", "-q", "-b", "feat/test")
        self.git("push", "-q", "-u", "origin", "feat/test")
        (self.repo / "data" / "act1_nodes.json").write_text('{"grown": true}')
        (self.repo / "data" / "walk_new.json").write_text("{}")  # untracked file
        self.assertTrue(self.evolve.commit_data_changes(self.repo))
        self.assertEqual(self.git("status", "--porcelain").stdout.strip(), "")
        remote = self.git("log", "--format=%s", "origin/feat/test", "-1").stdout
        self.assertIn("chore(organism)", remote)
        self.assertIn("act1_nodes.json", remote)

    def test_never_commits_on_main(self):
        (self.repo / "data" / "act1_nodes.json").write_text('{"grown": true}')
        self.assertFalse(self.evolve.commit_data_changes(self.repo))
        self.assertIn("act1_nodes.json", self.git("status", "--porcelain").stdout)
        self.assertEqual(self.git("log", "--format=%s", "-1").stdout.strip(), "init")

    def test_ignores_non_data_changes(self):
        self.git("checkout", "-q", "-b", "feat/test")
        (self.repo / "evolve.py").write_text("# changed code")
        self.assertFalse(self.evolve.commit_data_changes(self.repo))
        self.assertIn("evolve.py", self.git("status", "--porcelain").stdout)


if __name__ == "__main__":
    unittest.main()
