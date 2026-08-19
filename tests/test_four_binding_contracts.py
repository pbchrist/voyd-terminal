"""Deterministic contract-route tests for the selected Four Binding Contracts mutation."""
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_IDS = (
    "demanded_identity",
    "claimed_knowledge",
    "demanded_motive",
    "identity_as_bait",
)
REQUIRED_STATE = {
    "identity",
    "terms",
    "initiative",
    "resolution",
    "unpaid_cost",
    "choice_history",
    "personal_referent",
    "exposed_risk",
    "reciprocal_demand",
    "explicit_test",
}


def load_headless():
    spec = importlib.util.spec_from_file_location("headless_play", ROOT / "scripts/headless_play.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def route_chooser(entry, opening, later=1):
    def choose(*, node, choices=None, open_input=False, **_):
        if open_input:
            return "the future i am choosing now"
        if node["id"] == "1.0":
            return entry
        if node["id"] in {"2.1", "2.2"}:
            return opening
        return later
    return choose


class FourBindingContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "data/act1_nodes.json").read_text())
        cls.nodes = cls.data["nodes"]
        cls.headless = load_headless()

    def walk(self, entry, opening, later=1):
        with mock.patch.object(self.headless, "qwen_chat", return_value="act two"):
            return self.headless.play(
                chooser=route_chooser(entry, opening, later),
                act1_data=self.data,
            )

    def test_opening_actions_create_four_distinct_complete_contracts(self):
        openings = [
            self.nodes["2.1"]["choices"][0],
            self.nodes["2.1"]["choices"][1],
            self.nodes["2.2"]["choices"][1],
            self.nodes["2.2"]["choices"][0],
        ]
        self.assertEqual([c["contract_start"]["identity"] for c in openings], list(CONTRACT_IDS))
        self.assertEqual(len({c["next"] for c in openings}), 4)
        for choice in openings:
            contract = choice["contract_start"]
            self.assertTrue(REQUIRED_STATE - {"choice_history"} <= set(contract))
            self.assertTrue(contract["terms"])
            self.assertTrue(contract["exposed_risk"])
            self.assertTrue(contract["reciprocal_demand"])
            self.assertTrue(contract["explicit_test"])
            immediate = self.nodes[choice["next"]]
            self.assertEqual(immediate["contract_stage"], "return")
            self.assertEqual(immediate["contract_identity"], contract["identity"])

    def test_demanded_identity_returns_a_usable_truth_immediately(self):
        route = self.walk(1, 1)
        immediate = route["node_texts"][2].lower()
        self.assertIn("intention", immediate)
        self.assertIn("genuine release", immediate)
        self.assertIn("starve", immediate)
        self.assertEqual(route["contract"]["identity"], "demanded_identity")

    def test_opposed_routes_differ_immediately_and_at_act2_reconvergence(self):
        routes = {
            "demanded_identity": self.walk(1, 1),
            "claimed_knowledge": self.walk(1, 2),
            "demanded_motive": self.walk(2, 2),
            "identity_as_bait": self.walk(2, 1),
        }
        immediate_nodes = {r["path"][2] for r in routes.values()}
        immediate_returns = {r["node_texts"][2] for r in routes.values()}
        self.assertEqual(len(immediate_nodes), 4)
        self.assertEqual(len(immediate_returns), 4)

        outcomes = set()
        act2_openings = set()
        for expected, route in routes.items():
            contract = route["contract"]
            self.assertEqual(contract["identity"], expected)
            self.assertIn(contract["resolution"], {"paid", "fulfilled", "accepted", "refused", "breached"})
            self.assertIsNotNone(contract["personal_referent"])
            self.assertGreaterEqual(len(contract["choice_history"]), 3)
            self.assertIn(expected, route["act2_prompt"])
            self.assertIn("Contract terms:", route["act2_prompt"])
            self.assertIn("Initiative:", route["act2_prompt"])
            self.assertIn("Unpaid cost:", route["act2_prompt"])
            self.assertIn("Personal referent:", route["act2_prompt"])
            self.assertIn(expected.replace("_", " "), route["act2_opening"])
            act2_openings.add(route["act2_opening"])
            outcomes.add((
                contract["identity"], tuple(contract["terms"]), contract["resolution"],
                contract["unpaid_cost"], tuple(contract["choice_history"]),
            ))
        self.assertEqual(len(outcomes), 4)
        self.assertEqual(len(act2_openings), 4)

    def test_paid_and_breached_runs_have_irreversibly_different_outcomes(self):
        paid = self.walk(1, 1, later=1)["contract"]
        breached = self.walk(1, 1, later=2)["contract"]
        self.assertNotEqual(paid["resolution"], breached["resolution"])
        self.assertNotEqual(paid["unpaid_cost"], breached["unpaid_cost"])
        self.assertNotEqual(paid["initiative"], breached["initiative"])
        self.assertNotEqual(paid["choice_history"], breached["choice_history"])

    def test_browser_contract_runtime_matches_headless_schema(self):
        script = r"""
const c = require('./frontend/contract_state.js');
let s = c.createContractState();
s = c.applyContractChoice(s, {
  contract_start: {
    identity: 'demanded_identity', terms: ['truth for disclosure'], initiative: 'player',
    resolution: 'active', unpaid_cost: null, personal_referent: null,
    exposed_risk: 'starvation rule exposed', reciprocal_demand: 'choose a referent',
    explicit_test: 'use the rule'
  }, contract_action: 'demand_identity'
});
s = c.applyContractChoice(s, {
  contract_update: {personal_referent: 'another person', resolution: 'paid'},
  contract_action: 'release_claim'
});
process.stdout.write(JSON.stringify(s));
"""
        result = subprocess.run(
            ["node", "-e", script], cwd=ROOT, check=True, text=True, capture_output=True
        )
        browser_state = json.loads(result.stdout)
        self.assertEqual(set(browser_state), REQUIRED_STATE)
        self.assertEqual(browser_state["choice_history"], ["demand_identity", "release_claim"])
        self.assertEqual(browser_state["personal_referent"], "another person")
        frontend = ((ROOT / "frontend/index.html").read_text() +
                    (ROOT / "frontend/contract_state.js").read_text())
        self.assertIn("applyContractChoice(contract, choice)", frontend)
        self.assertIn("contract: options.contract", frontend)
        for field in REQUIRED_STATE:
            self.assertIn(field, frontend)

    def test_browser_proxy_transports_and_enforces_contract(self):
        html = (ROOT / "frontend" / "index.html").read_text()
        self.assertIn("contract: result.state.contract", html)
        self.assertIn("contract_opening: VoydContracts.contractOpening(result.state.contract)", html)
        self.assertIn("system_prompt: result.systemPrompt", html)
        self.assertIn("result.state.depth === 1 && result.state.contract.identity", html)
        self.assertIn("voydText = opening + '\\n\\n' + voydText", html)


if __name__ == "__main__":
    unittest.main()
