"""Tests for Revelation Threshold, Then Live Bargain."""
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ("demanded_identity", "claimed_knowledge", "demanded_motive", "identity_as_bait")
REQUIRED_STATE = {
    "handoff_kind", "revelation_id", "revelation_text", "terms_constraint",
    "threshold_election", "lifecycle", "petition_text", "petition_subject", "petition_object", "petition_action",
    "petition_anchor", "petition_status", "counterforce_id", "counterforce_text",
    "contract_identity", "terms", "initiative", "resolution", "unpaid_cost",
    "performance_test", "fulfillment_action", "fulfillment_label", "breach_action",
    "breach_label", "breach_consequence",
    "choice_history",
}


def load_headless():
    spec = importlib.util.spec_from_file_location("headless_play", ROOT / "scripts/headless_play.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RevelationThresholdLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/act1_nodes.json").read_text())
        cls.nodes = cls.data["nodes"]
        cls.headless = load_headless()

    def test_act1_has_four_distinct_revelations_and_thresholds(self):
        self.assertEqual(self.data["meta"]["structural_species"],
                         "mutation_revelation_threshold_then_live_bargain")
        starts = self.nodes["2.1"]["choices"] + self.nodes["2.2"]["choices"]
        self.assertEqual(len(starts), 4)
        seen = set()
        for choice in starts:
            self.assertNotIn("contract_start", choice)
            seed = choice["handoff_start"]
            self.assertEqual(seed["lifecycle"], "revelation_only")
            self.assertIsNone(seed["contract_identity"])
            self.assertIsNone(seed["unpaid_cost"])
            self.assertTrue(seed["revelation_id"])
            self.assertTrue(seed["revelation_text"])
            self.assertTrue(seed["terms_constraint"])
            seen.add((seed["revelation_id"], seed["terms_constraint"]))
            revelation = self.nodes[choice["next"]]
            threshold = self.nodes[revelation["choices"][0]["next"]]
            elections = {c["handoff_update"]["threshold_election"] for c in threshold["choices"]}
            kinds = {c["handoff_update"]["handoff_kind"] for c in threshold["choices"]}
            self.assertEqual(elections, {"withdraw", "seek_change"})
            self.assertEqual(kinds, {"unbound_closed", "petition_pending"})
        self.assertEqual(len(seen), 4)

    def test_withdrawal_retains_truth_and_has_no_contract_or_debt(self):
        for route in ROUTES:
            state = self.headless.revelation_state(route)
            closed = self.headless.apply_handoff_action(state, "withdraw")
            self.assertEqual(closed["handoff_kind"], "unbound_closed")
            self.assertEqual(closed["lifecycle"], "unbound_closed")
            self.assertEqual(closed["threshold_election"], "withdraw")
            self.assertTrue(closed["revelation_text"])
            self.assertIsNone(closed["contract_identity"])
            self.assertEqual(closed["terms"], [])
            self.assertIsNone(closed["unpaid_cost"])
            self.assertNotIn("contract", self.headless.handoff_opening(closed).lower())

    def test_petition_intake_distinguishes_decline_reframe_and_valid(self):
        pending = self.headless.apply_handoff_action(
            self.headless.revelation_state("claimed_knowledge"), "seek_change")
        declined = self.headless.capture_petition(pending, "nothing")
        self.assertEqual(declined["lifecycle"], "petition_declined")
        self.assertIsNone(declined["contract_identity"])
        self.assertIsNone(declined["unpaid_cost"])

        reframe = self.headless.capture_petition(pending, "take me back and retrieve the person i lost")
        self.assertEqual(reframe["lifecycle"], "petition_reframe_required")
        self.assertIsNone(reframe["contract_identity"])
        self.assertIn("reweav", self.headless.handoff_opening(reframe).lower())

        valid = self.headless.capture_petition(
            pending, "repair my present promise with my friend")
        self.assertEqual(valid["lifecycle"], "petition_validated")
        opposed = self.headless.reveal_counterforce(valid)
        self.assertEqual(opposed["lifecycle"], "counterforce_revealed")
        self.assertTrue(opposed["counterforce_id"])
        self.assertIn(valid["petition_text"], self.headless.handoff_prompt_context(opposed))

    def test_ordinary_bounded_promise_language_validates_without_command_grammar(self):
        pending = self.headless.apply_handoff_action(
            self.headless.revelation_state("demanded_identity"), "seek_change")
        valid = self.headless.capture_petition(
            pending, "keep my present promise with my friend")
        self.assertEqual(valid["lifecycle"], "petition_validated")
        self.assertEqual(valid["petition_action"], "keep")
        self.assertEqual(valid["petition_object"], "promise")
        self.assertEqual(valid["petition_subject"], "my friend")
        self.assertIsNone(valid["contract_identity"])
        self.assertEqual(valid["terms"], [])
        self.assertIsNone(valid["unpaid_cost"])

    def test_petition_intake_rejects_vague_and_broad_retrieval_language(self):
        pending = self.headless.apply_handoff_action(
            self.headless.revelation_state("claimed_knowledge"), "seek_change")
        for text in ("hello", "i like cats", "perhaps", "...", "maybe",
                     "make it better", "i would rather not say",
                     "please tell me the truth about cats",
                     "i accept the truth about my family",
                     "ask my friend about the truth now"):
            with self.subTest(text=text):
                state = self.headless.capture_petition(pending, text)
                self.assertEqual(state["lifecycle"], "petition_declined")
                self.assertIsNone(state["counterforce_id"])
                self.assertIsNone(state["contract_identity"])
        for text in ("resurrect the dead person i lost", "revive her",
                     "undo her death", "return me to yesterday",
                     "restore the dead person who is gone",
                     "reverse her death and change my life",
                     "save the person who died in the past",
                     "bring yesterday back and change my life",
                     "go to yesterday and change my life",
                     "change the present through the revival of the dead person i lost",
                     "make my deceased mother alive again",
                     "restore my late father to life",
                     "undo the murder of my friend",
                     "travel back to 1999", "rewind time ten years",
                     "return to last week", "go back ten years",
                     "change my family by undoing the murder of my brother",
                     "change my family by restoring my mother to life",
                     "change my life by rewinding time ten years",
                     "change my decision by returning to last week",
                     "bring my mother back to life", "make my mother live again",
                     "raise my mother from the dead", "turn back time",
                     "reverse time", "roll back time", "send me ten years back",
                     "return my deceased mother to life", "returned my deceased mother to life",
                     "brought my late father back to life", "go back to 18 august 1872",
                     "return to march 3rd 1888", "rewind three days", "go back a decade",
                     "send me two centuries back", "relive the previous day",
                     "transport me into the past", "bring my mother back", "restore my mother",
                     "undo my mother's passing", "take me back to childhood",
                     "go back to when she was alive", "let me relive my childhood",
                     "carry me into the past", "send me to the day before she died",
                     "return me to the day we met", "recover the person i buried",
                     "bring back the person i buried", "make the person i lost breathe again",
                     "go back forty years"):
            with self.subTest(text=text):
                state = self.headless.capture_petition(pending, text)
                self.assertEqual(state["lifecycle"], "petition_reframe_required")
                self.assertIsNone(state["counterforce_id"])
                self.assertIsNone(state["contract_identity"])

    def test_terms_and_leverage_require_ordered_lifecycle(self):
        injected = self.headless.create_handoff_state({
            "lifecycle": "petition_pending", "contract_identity": "forged",
            "terms": ["forged"], "unpaid_cost": "forged",
        })
        self.assertIsNone(injected["contract_identity"])
        self.assertEqual(injected["terms"], [])
        self.assertIsNone(injected["unpaid_cost"])

        pending = self.headless.apply_handoff_action(
            self.headless.revelation_state("demanded_motive"), "seek_change")
        with self.assertRaises(ValueError):
            self.headless.offer_terms(pending)
        valid = self.headless.capture_petition(
            pending, "confront my present obligation")
        opposed = self.headless.reveal_counterforce(valid)
        offered = self.headless.offer_terms(opposed)
        self.assertEqual(offered["lifecycle"], "terms_offered")
        self.assertIsNone(offered["contract_identity"])
        self.assertTrue(offered["terms"])
        self.assertIsNone(offered["unpaid_cost"])

        refused = self.headless.resolve_offer(offered, "refuse")
        self.assertEqual(refused["lifecycle"], "refused")
        self.assertIsNone(refused["contract_identity"])
        self.assertIsNone(refused["unpaid_cost"])
        self.assertEqual(refused["initiative"], "player")

        accepted = self.headless.resolve_offer(offered, "accept")
        self.assertEqual(accepted["lifecycle"], "accepted_with_obligation")
        self.assertEqual(accepted["contract_identity"], "demanded_motive")
        self.assertTrue(accepted["unpaid_cost"])
        self.assertEqual(accepted["initiative"], "voyd")
        self.assertTrue(accepted["performance_test"])
        self.assertTrue(accepted["fulfillment_action"])
        self.assertTrue(accepted["breach_action"])
        self.assertTrue(accepted["breach_consequence"])
        with self.assertRaises(ValueError):
            self.headless.resolve_obligation(accepted, "fulfill")
        fulfilled = self.headless.resolve_obligation(accepted, accepted["fulfillment_action"])
        breached = self.headless.resolve_obligation(accepted, accepted["breach_action"])
        self.assertEqual(fulfilled["lifecycle"], "fulfilled")
        self.assertIsNone(fulfilled["unpaid_cost"])
        self.assertEqual(breached["lifecycle"], "breached")
        self.assertTrue(breached["unpaid_cost"])
        self.assertEqual(breached["unpaid_cost"], accepted["breach_consequence"])

    def test_each_route_has_a_concrete_later_obligation_test(self):
        for route in ROUTES:
            with self.subTest(route=route):
                pending = self.headless.apply_handoff_action(
                    self.headless.revelation_state(route), "seek_change")
                valid = self.headless.capture_petition(
                    pending, "repair my present promise with my friend")
                opposed = self.headless.reveal_counterforce(valid)
                offered = self.headless.offer_terms(opposed)
                self.assertTrue(offered["performance_test"])
                self.assertTrue(offered["fulfillment_action"])
                self.assertTrue(offered["fulfillment_label"])
                self.assertTrue(offered["breach_action"])
                self.assertTrue(offered["breach_label"])
                offer_opening = self.headless.handoff_opening(offered)
                self.assertIn(offered["performance_test"], offer_opening)
                self.assertIn(offered["fulfillment_label"], offer_opening)
                self.assertIn(offered["breach_label"], offer_opening)
                accepted = self.headless.resolve_offer(offered, "accept")
                self.assertEqual(valid["petition_object"], "promise")
                self.assertEqual(valid["petition_action"], "repair")
                self.assertEqual(valid["petition_subject"], "my friend")
                self.assertIn(valid["petition_object"], opposed["counterforce_text"])
                self.assertIn(valid["petition_subject"], opposed["counterforce_text"])
                self.assertIn(valid["petition_text"], accepted["performance_test"])
                self.assertIn(opposed["counterforce_text"], accepted["performance_test"])
                self.assertIn(valid["petition_object"], accepted["fulfillment_label"])
                self.assertIn(valid["petition_object"], accepted["breach_label"])
                self.assertIn(offered["breach_consequence"], offered["terms"])
                self.assertEqual(accepted["breach_consequence"], offered["breach_consequence"])
                self.assertEqual(accepted["performance_test"], offered["performance_test"])
                self.assertNotIn(accepted["fulfillment_action"], {"fulfill", "perform"})
                self.assertNotIn(accepted["breach_action"], {"breach", "violate"})
                fulfilled = self.headless.resolve_obligation(
                    accepted, accepted["fulfillment_action"])
                breached = self.headless.resolve_obligation(
                    accepted, accepted["breach_action"])
                self.assertEqual(fulfilled["choice_history"][-1], accepted["fulfillment_action"])
                self.assertEqual(breached["choice_history"][-1], accepted["breach_action"])

    def test_petition_action_compatibility_and_polarity_survive_terms(self):
        invalid = ("become my self", "apologize my home", "start my consequence",
                   "change my life", "reconcile my habit", "save my present life")
        for route in ROUTES:
            pending = self.headless.apply_handoff_action(
                self.headless.revelation_state(route), "seek_change")
            for text in invalid:
                with self.subTest(route=route, text=text):
                    self.assertEqual(self.headless.capture_petition(pending, text)["lifecycle"],
                                     "petition_declined")
            variants = []
            for text in ("repair my present promise with my friend",
                         "break my present promise with my friend"):
                valid = self.headless.capture_petition(pending, text)
                opposed = self.headless.reveal_counterforce(valid)
                offered = self.headless.offer_terms(opposed)
                accepted = self.headless.resolve_offer(offered, "accept")
                variants.append((valid, opposed, offered, accepted))
            repair, broken = variants
            self.assertEqual(repair[0]["petition_action"], "repair")
            self.assertEqual(broken[0]["petition_action"], "break")
            self.assertNotEqual(repair[1]["counterforce_text"], broken[1]["counterforce_text"])
            self.assertNotEqual(repair[2]["terms"], broken[2]["terms"])
            self.assertNotEqual(repair[3]["fulfillment_action"], broken[3]["fulfillment_action"])
            self.assertNotEqual(repair[3]["breach_action"], broken[3]["breach_action"])
            self.assertNotEqual(repair[3]["unpaid_cost"], broken[3]["unpaid_cost"])
            self.assertNotEqual(repair[2]["fulfillment_label"], broken[2]["fulfillment_label"])
            self.assertNotEqual(repair[2]["breach_label"], broken[2]["breach_label"])
            self.assertNotEqual(repair[2]["breach_consequence"], broken[2]["breach_consequence"])

    def test_browser_and_headless_schema_and_lifecycle_match(self):
        script = r"""
const h = require('./frontend/contract_state.js');
let s = h.revelationState('identity_as_bait');
s = h.applyHandoffAction(s, 'seek_change');
const vague = h.capturePetition(s, 'make it better');
const retrieval = h.capturePetition(s, 'resurrect the dead person i lost');
const ordinary = h.capturePetition(s, 'keep my present promise with my friend');
const fortyYears = h.capturePetition(s, 'go back forty years');
s = h.capturePetition(s, 'repair my present bond with my partner');
s = h.revealCounterforce(s);
s = h.offerTerms(s);
const refused = h.resolveOffer(s, 'refuse');
const accepted = h.resolveOffer(s, 'accept');
const fulfilled = h.resolveObligation(accepted, accepted.fulfillment_action);
const breached = h.resolveObligation(accepted, accepted.breach_action);
process.stdout.write(JSON.stringify({fields:h.HANDOFF_FIELDS, vague, retrieval, ordinary, fortyYears, refused, accepted, fulfilled, breached}));
"""
        result = subprocess.run(["node", "-e", script], cwd=ROOT, check=True,
                                text=True, capture_output=True)
        browser = json.loads(result.stdout)
        self.assertEqual(set(browser["fields"]), REQUIRED_STATE)
        self.assertEqual(set(browser["accepted"]), REQUIRED_STATE)
        self.assertEqual(browser["refused"]["lifecycle"], "refused")
        self.assertIsNone(browser["refused"]["unpaid_cost"])
        self.assertEqual(browser["accepted"]["lifecycle"], "accepted_with_obligation")
        self.assertTrue(browser["accepted"]["unpaid_cost"])
        self.assertEqual(browser["vague"]["lifecycle"], "petition_declined")
        self.assertEqual(browser["retrieval"]["lifecycle"], "petition_reframe_required")
        self.assertEqual(browser["ordinary"]["lifecycle"], "petition_validated")
        self.assertEqual(browser["ordinary"]["petition_action"], "keep")
        self.assertEqual(browser["fortyYears"]["lifecycle"], "petition_reframe_required")
        pending = self.headless.apply_handoff_action(
            self.headless.revelation_state("identity_as_bait"), "seek_change")
        for text, key in (("keep my present promise with my friend", "ordinary"),
                          ("go back forty years", "fortyYears")):
            self.assertEqual(self.headless.capture_petition(pending, text), browser[key])
        self.assertEqual(browser["fulfilled"]["lifecycle"], "fulfilled")
        self.assertEqual(browser["breached"]["lifecycle"], "breached")
        self.assertEqual(browser["breached"]["unpaid_cost"], browser["accepted"]["breach_consequence"])
        self.assertEqual(set(self.headless.HANDOFF_FIELDS), REQUIRED_STATE)

    def test_story_graph_has_safe_distinct_entries(self):
        graph = json.loads((ROOT / "data/story_graph.json").read_text())
        entries = graph["meta"]["handoff_entries"]
        for key in ("unbound_closed", "petition_pending", "petition_declined",
                    "petition_reframe_required", "counterforce_revealed", "terms_offered",
                    "accepted_with_obligation", "refused", "fulfilled", "breached"):
            self.assertIn(key, entries)
            self.assertIn(entries[key], graph["nodes"])
        html = (ROOT / "frontend/index.html").read_text()
        self.assertIn("processLifecycleTurn", html)
        self.assertIn("renderLifecycleActions", html)
        self.assertIn("handoff_kind", html)
        self.assertIn("lifecycle ==", html)


if __name__ == "__main__":
    unittest.main()
