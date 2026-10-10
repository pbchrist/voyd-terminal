#!/usr/bin/env python3
"""Headless Voyd traversal and deterministic live-bargain lifecycle."""
import json
import re
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ACT1_PATH = REPO_ROOT / "data" / "act1_nodes.json"
VOICE_PATH = REPO_ROOT / "data" / "voyd_system.md"
QWEN_URL = "http://localhost:8081/v1/chat/completions"
QWEN_MODEL = "Qwen3.6-27B-Q6_K"

HANDOFF_FIELDS = (
    "handoff_kind", "revelation_id", "revelation_text", "terms_constraint",
    "threshold_election", "lifecycle", "petition_text", "petition_subject", "petition_object", "petition_action",
    "petition_anchor", "petition_status", "counterforce_id", "counterforce_text",
    "contract_identity", "terms", "initiative", "resolution", "unpaid_cost",
    "performance_test", "fulfillment_action", "fulfillment_label", "breach_action",
    "breach_label", "breach_consequence", "choice_history",
)

REVELATIONS = {
    "demanded_identity": {
        "revelation_id": "release_starves_intention",
        "revelation_text": "intention gives the Voyd purchase on the unfinished present, while genuine release starves that purchase.",
        "terms_constraint": "any offer must preserve genuine release as an available end to the Voyd's pressure and cannot promise retrieval.",
    },
    "claimed_knowledge": {
        "revelation_id": "reweaving_is_not_retrieval",
        "revelation_text": "the Voyd stores no completed life or earlier self; intention may reach a pivotal moment only to reweave the resulting present amid competing wills and collateral change.",
        "terms_constraint": "any offer must name forward reweaving of the present, never backward travel, retrieval, or a stored life.",
    },
    "demanded_motive": {
        "revelation_id": "intention_is_the_appetite",
        "revelation_text": "the Voyd recruits sustained intention because a living plan feeds it, but it cannot erase competing wills or collateral consequences.",
        "terms_constraint": "any offer may apply one bounded pressure to the unfinished present and must leave competing wills and consequences intact.",
    },
    "identity_as_bait": {
        "revelation_id": "possibility_is_a_lure",
        "revelation_text": "the identity called possibility is a recruiting lure: its image is proposed, not a person or outcome stored for recovery.",
        "terms_constraint": "any offer must identify the image as a proposed future and may grant only one disclosed, bounded use of that lure.",
    },
}
COUNTERFORCES = {
    "demanded_identity": ("competing_will", "the will touched by the requested change can refuse the direction placed upon it."),
    "claimed_knowledge": ("collateral_consequences", "reweaving the present preserves every competing will and changes consequences beyond the requested result."),
    "demanded_motive": ("existing_obligation", "the requested change collides with an obligation already active in the present and cannot erase it."),
    "identity_as_bait": ("required_sacrifice", "to pursue the proposed image, the player must release the comforting belief that the desired outcome already exists somewhere to be recovered."),
}
OFFERS = {
    "demanded_identity": {
        "terms": ["apply one bounded pressure toward the stated petition", "the affected will remains free to refuse", "genuine release ends the Voyd's leverage"],
        "cost": "the Voyd may press the stated petition once, until the player genuinely releases that direction",
    },
    "claimed_knowledge": {
        "terms": ["reweave only the present consequences named in the petition", "no backward travel or stored life is promised", "collateral consequences remain real"],
        "cost": "the player must answer for the collateral consequence revealed beside the petition",
    },
    "demanded_motive": {
        "terms": ["authorize one bounded pressure toward the stated petition", "the existing obligation and competing wills remain", "no past event is returned"],
        "cost": "one authorized pressure toward the petition remains to be answered for",
    },
    "identity_as_bait": {
        "terms": ["treat the desired image as a proposed future, never a stored outcome", "authorize one disclosed use of that image as leverage", "the image expires after that use"],
        "cost": "the disclosed proposed image may be used once as leverage and no more",
    },
}
OBLIGATION_TESTS = {
    "demanded_identity": {
        "test": "{subject} refuses the directed change to {object} inside '{petition}'. {counterforce} release that direction now, or continue it knowingly.",
        "fulfillment_action": "release_directed_pressure", "fulfillment_label": "release my direction to {action} {subject}'s {object}",
        "breach_action": "continue_directed_pressure", "breach_label": "continue directing the action {action} over {subject}'s {object}",
        "breach_consequence": "the Voyd may use the continued action {action} over {subject}'s {object} once as leverage until it is genuinely released",
    },
    "claimed_knowledge": {
        "test": "{subject} invokes the disclosed right to treat {object} as void after '{petition}' reweaves it. {counterforce} acknowledge that loss of enforceability, or deny it by calling the reweaving retrieval.",
        "fulfillment_action": "acknowledge_collateral_consequence", "fulfillment_label": "acknowledge {subject}'s right to treat the action {action} on {object} as void",
        "breach_action": "misname_change_as_retrieval", "breach_label": "deny {subject}'s right over the action {action} on {object} and call it retrieval",
        "breach_consequence": "the Voyd holds denial of {subject}'s disclosed right over the action {action} on {object} as leverage",
    },
    "demanded_motive": {
        "test": "{subject} refuses pressure on {object} before '{petition}' can proceed. {counterforce} preserve that refusal, or discard it to preserve the desired result.",
        "fulfillment_action": "honor_existing_obligation", "fulfillment_label": "preserve {subject}'s refusal of the action {action} on {object}",
        "breach_action": "discard_existing_obligation", "breach_label": "discard {subject}'s refusal of the action {action} on {object}",
        "breach_consequence": "the Voyd may collect pressure through the discarded refusal of the action {action} over {subject}'s {object}",
    },
    "identity_as_bait": {
        "test": "the proposed image of changed {subject}'s {object} behind '{petition}' now claims it was waiting here all along. {counterforce} release that false claim, or declare the image stored.",
        "fulfillment_action": "release_stored_outcome_belief", "fulfillment_label": "release the claim that the action {action} on {subject}'s {object} was stored",
        "breach_action": "claim_outcome_was_stored", "breach_label": "claim the image created by {action} on {subject}'s {object} was stored",
        "breach_consequence": "the Voyd may use the falsely stored image created by {action} on {subject}'s {object} once as leverage",
    },
}
LEGAL = {
    "revelation_only": {"unbound_closed", "petition_pending"},
    "petition_pending": {"petition_declined", "petition_reframe_required", "petition_validated"},
    "petition_reframe_required": {"petition_declined", "petition_reframe_required", "petition_validated"},
    "petition_declined": {"petition_pending", "unbound_closed"},
    "petition_validated": {"counterforce_revealed"},
    "counterforce_revealed": {"terms_offered"},
    "terms_offered": {"refused", "accepted_with_obligation"},
    "accepted_with_obligation": {"fulfilled", "breached"},
    "unbound_closed": set(), "refused": set(), "fulfilled": set(), "breached": set(),
}
ACTION_OBJECTS = {
    "relationship": {"repair", "rebuild", "reconcile", "release", "end", "protect", "mend", "break"},
    "promise": {"repair", "release", "end", "protect", "break", "commit", "keep", "honor", "maintain", "fulfill"},
    "obligation": {"change", "alter", "release", "end", "protect", "confront", "commit"},
    "consequence": {"change", "alter", "reweave", "confront", "prevent"},
    "course": {"change", "alter", "reweave"},
    "bond": {"repair", "rebuild", "reconcile", "release", "end", "protect", "mend", "break"},
    "self": {"change", "alter", "rebuild"}, "life": {"alter", "rebuild", "protect"},
    "decision": {"change", "alter", "reweave", "confront"},
    "work": {"change", "alter", "rebuild", "protect", "end"},
    "home": {"repair", "rebuild", "protect", "leave"},
    "habit": {"change", "alter", "end", "stop", "start", "break"},
    "fear": {"confront", "release", "end"}, "grief": {"confront", "release"},
    "claim": {"release", "end", "protect", "break"},
    "direction": {"change", "alter", "release", "end", "protect"},
    "commitment": {"start", "end", "protect", "break", "commit"},
}


def load_voice_prompt():
    try:
        return VOICE_PATH.read_text(encoding="utf-8").strip()
    except OSError:
        return "You are the Voyd. Speak in short, lowercase, declarative sentences."


def qwen_chat(messages, max_tokens=300, temperature=0.9):
    payload = {"model": QWEN_MODEL, "max_tokens": max_tokens, "temperature": temperature,
               "messages": messages, "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(QWEN_URL, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"]


def create_handoff_state(seed=None):
    state = {
        "handoff_kind": "revelation_only", "revelation_id": None,
        "revelation_text": None, "terms_constraint": None,
        "threshold_election": None, "lifecycle": "revelation_only",
        "petition_text": None, "petition_subject": None, "petition_object": None, "petition_action": None, "petition_anchor": None,
        "petition_status": None, "counterforce_id": None, "counterforce_text": None,
        "contract_identity": None, "terms": [], "initiative": "player",
        "resolution": None, "unpaid_cost": None, "performance_test": None,
        "fulfillment_action": None, "fulfillment_label": None,
        "breach_action": None, "breach_label": None, "breach_consequence": None,
        "choice_history": [],
    }
    for field in HANDOFF_FIELDS:
        if seed and field in seed:
            value = seed[field]
            state[field] = list(value) if isinstance(value, list) else value
    pre_terms = {"revelation_only", "unbound_closed", "petition_pending", "petition_declined",
                 "petition_reframe_required", "petition_validated", "counterforce_revealed"}
    if state["lifecycle"] in pre_terms:
        state["contract_identity"], state["terms"], state["unpaid_cost"] = None, [], None
        state["performance_test"] = state["fulfillment_action"] = None
        state["fulfillment_label"] = state["breach_action"] = None
        state["breach_label"] = state["breach_consequence"] = None
    elif state["lifecycle"] in {"terms_offered", "refused", "fulfilled"}:
        state["unpaid_cost"] = None
    return state


def revelation_state(route):
    if route not in REVELATIONS:
        raise ValueError(f"unknown revelation route: {route}")
    return create_handoff_state({"handoff_kind": "revelation_only", "lifecycle": "revelation_only",
                                 "initiative": "player", **REVELATIONS[route]})


def _transition(current, lifecycle, update=None, action=None):
    state = create_handoff_state(current)
    if lifecycle not in LEGAL.get(state["lifecycle"], set()):
        raise ValueError(f"illegal lifecycle transition: {state['lifecycle']} -> {lifecycle}")
    state["lifecycle"] = lifecycle
    state.update(update or {})
    if action:
        state["choice_history"].append(action)
    return create_handoff_state(state)


def apply_handoff_choice(current, choice):
    state = create_handoff_state(choice.get("handoff_start") or current)
    update = dict(choice.get("handoff_update") or {})
    target = update.pop("lifecycle", None)
    if target and target != state["lifecycle"]:
        return _transition(state, target, update, choice.get("handoff_action"))
    state.update({k: v for k, v in update.items() if k in HANDOFF_FIELDS})
    if choice.get("handoff_action"):
        state["choice_history"].append(choice["handoff_action"])
    return create_handoff_state(state)


def apply_handoff_action(current, action):
    if action == "withdraw":
        return _transition(current, "unbound_closed", {
            "handoff_kind": "unbound_closed", "threshold_election": "withdraw",
            "initiative": "player", "resolution": None, "contract_identity": None,
            "terms": [], "unpaid_cost": None}, "withdraw_with_truth")
    if action == "seek_change":
        return _transition(current, "petition_pending", {
            "handoff_kind": "petition_pending", "threshold_election": "seek_change",
            "initiative": "player", "resolution": None, "contract_identity": None,
            "terms": [], "unpaid_cost": None}, "seek_concrete_change")
    if action == "reopen_petition":
        return _transition(current, "petition_pending", {
            "handoff_kind": "petition_pending", "petition_status": None}, "state_change_after_declining")
    if action == "close_unbound":
        return _transition(current, "unbound_closed", {
            "handoff_kind": "unbound_closed", "initiative": "player"}, "close_without_bargain")
    raise ValueError(f"unknown handoff action: {action}")


def capture_petition(current, text):
    state = create_handoff_state(current)
    if state["lifecycle"] not in {"petition_pending", "petition_reframe_required"}:
        raise ValueError(f"petition cannot be captured from {state['lifecycle']}")
    raw = str(text or "").strip()
    lower = raw.lower()
    words = re.findall(r"[a-z']+", lower)
    petition_match = re.fullmatch(
        r"(?:please\s+)?(?:i\s+(?:want|need|choose|intend|seek|ask)\s+to\s+)?"
        r"(change|alter|reweave|repair|rebuild|reconcile|release|end|stop|start|begin|become|leave|protect|break|commit|keep|honor|maintain|fulfill|forgive|apologize|confront|prevent|save|free|move|finish|mend|press)\s+"
        r"(?:my|the|a)\s+(?:present\s+)?"
        r"(relationship|promise|obligation|consequence|course|bond|self|life|decision|work|home|habit|fear|grief|claim|direction|commitment)"
        r"(?:\s+(?:with|about|toward|for)\s+(myself|another person|my family|my friend|my partner))?[.!?]*", lower)
    petition_object = petition_match.group(2) if petition_match else None
    petition_action = petition_match.group(1) if petition_match else None
    compatible = bool(petition_object and petition_action and petition_action in ACTION_OBJECTS[petition_object])
    person_marker = re.search(r"\b(mother|father|brother|sister|wife|husband|person|friend|she|he|her|him|someone|anyone)\b", lower)
    death_marker = re.search(r"\b(dead|death|died|dying|gone|deceased|late|killed|murdered|murder|killing|passing|passed away|buried|lost|life|alive|breathe|live again)\b", lower)
    restore_marker = re.search(r"\b(resurrect\w*|reviv\w*|restor\w*|recover\w*|bring\w*|brought|make\w*|raise\w*|undo\w*|reverse\w*|save\w*|return\w*)\b", lower)
    death_return = restore_marker and (person_marker or death_marker)
    temporal_marker = re.search(r"\b(time|past|yesterday|earlier|childhood|previous day|day before|day we met|when .{0,20} alive|last (?:week|month|year)|(?:17|18|19|20)\d{2}|(?:(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|\d+) (?:days?|years?|months?|weeks?|decades?|centuries?)|a decade)\b", lower)
    temporal_move = re.search(r"\b(rewind\w*|reliv\w*|return\w*|travel\w*|transport\w*|carry\w*|take\w*|go|going|turn\w*|reverse\w*|roll\w*|send\w*|back)\b", lower)
    time_return = temporal_marker and temporal_move
    direct_false = re.search(r"\b(retriev\w*|resurrect\w*|reviv\w*)\b|stored (?:life|person|self)", lower)
    false_mechanism = not petition_match and (death_return or time_return or direct_false)
    if false_mechanism:
        return _transition(state, "petition_reframe_required", {
            "handoff_kind": "petition_reframe_required", "petition_text": raw,
            "petition_status": "reframe_required", "contract_identity": None,
            "terms": [], "unpaid_cost": None, "initiative": "player"}, "reject_retrieval_mechanism")
    evasive = (not raw or re.fullmatch(r"(nothing|never ?mind|i don't know|no change|pass|perhaps|maybe|i would rather not say)[.! ]*", lower)
               or len(words) < 3 or not petition_match or not compatible)
    if evasive:
        return _transition(state, "petition_declined", {
            "handoff_kind": "petition_declined", "petition_text": raw or None,
            "petition_status": "declined", "contract_identity": None, "terms": [],
            "unpaid_cost": None, "initiative": "player"}, "decline_petition")

    assert petition_match is not None
    subject = petition_match.group(3) or "myself"
    anchor = "pivotal_moment" if re.search(r"past|pivotal|moment|consequence|broke|before", lower) else "present_condition"
    return _transition(state, "petition_validated", {
        "handoff_kind": "petition_validated", "petition_text": raw,
        "petition_subject": subject, "petition_anchor": anchor,
        "petition_object": petition_object, "petition_action": petition_action,
        "petition_status": "validated", "initiative": "player",
        "contract_identity": None, "terms": [], "unpaid_cost": None}, "state_concrete_petition")


def _route_for(state):
    for route, revelation in REVELATIONS.items():
        if revelation["revelation_id"] == state.get("revelation_id"):
            return route
    raise ValueError("state has no known revelation")


def reveal_counterforce(current):
    state = create_handoff_state(current)
    if state["lifecycle"] != "petition_validated" or not state["petition_text"]:
        raise ValueError("counterforce requires a validated petition")
    route = _route_for(state)
    counter_id, _counter_text = COUNTERFORCES[route]
    object_ = state["petition_object"]
    subject = state["petition_subject"]
    action = state["petition_action"]
    concrete = {
        "demanded_identity": f"{subject} can refuse the action {action} applied to {object_}.",
        "claimed_knowledge": f"{action} applied through reweaving {object_} grants {subject} the disclosed right to treat it as void; that loss of enforceability is collateral.",
        "demanded_motive": f"{subject} can refuse the action {action} on {object_}; preserving that refusal limits the Voyd's appetite.",
        "identity_as_bait": f"the proposed image created by {action} on {subject}'s {object_} must be surrendered if it masquerades as stored.",
    }[route]
    return _transition(state, "counterforce_revealed", {
        "handoff_kind": "counterforce_revealed", "counterforce_id": counter_id,
        "counterforce_text": f"for '{state['petition_text']}', {concrete}",
        "initiative": "voyd"}, "counterforce_revealed")


def offer_terms(current):
    state = create_handoff_state(current)
    if state["lifecycle"] != "counterforce_revealed" or not state["petition_text"] or not state["counterforce_id"]:
        raise ValueError("terms require a petition-specific counterforce")
    route = _route_for(state)
    test = OBLIGATION_TESTS[route]
    values = {"petition": state["petition_text"], "counterforce": state["counterforce_text"],
              "object": state["petition_object"], "subject": state["petition_subject"],
              "action": state["petition_action"]}
    breach = test["breach_consequence"].format(**values)
    return _transition(state, "terms_offered", {
        "handoff_kind": "terms_offered", "contract_identity": None,
        "terms": OFFERS[route]["terms"] + [state["terms_constraint"],
                  f"the petition action remains {state['petition_action']}; no opposite action may be substituted", breach],
        "initiative": "player", "resolution": None, "unpaid_cost": None,
        "performance_test": test["test"].format(**values),
        "fulfillment_action": f"{test['fulfillment_action']}_{state['petition_action']}",
        "fulfillment_label": test["fulfillment_label"].format(**values),
        "breach_action": f"{test['breach_action']}_{state['petition_action']}",
        "breach_label": test["breach_label"].format(**values),
        "breach_consequence": breach}, "hear_constrained_terms")


def resolve_offer(current, action):
    state = create_handoff_state(current)
    if state["lifecycle"] != "terms_offered" or not state["terms"]:
        raise ValueError("an exact offer must exist first")
    route = _route_for(state)
    if action == "refuse":
        return _transition(state, "refused", {"handoff_kind": "refused", "initiative": "player",
                                               "contract_identity": None, "resolution": "refused",
                                               "unpaid_cost": None}, "refuse_exact_terms")
    if action == "accept":
        return _transition(state, "accepted_with_obligation", {
            "handoff_kind": "accepted_with_obligation", "initiative": "voyd",
            "contract_identity": route, "resolution": "accepted_with_obligation",
            "unpaid_cost": (f"{OFFERS[route]['cost']}: "
                            f"{state['petition_action']} {state['petition_object']} for {state['petition_subject']}")},
                           "accept_exact_terms")
    raise ValueError(f"unknown offer action: {action}")


def resolve_obligation(current, action):
    state = create_handoff_state(current)
    if state["lifecycle"] != "accepted_with_obligation" or not state["unpaid_cost"]:
        raise ValueError("no accepted obligation to resolve")
    if action == state["fulfillment_action"]:
        return _transition(state, "fulfilled", {"handoff_kind": "fulfilled", "initiative": "player",
                                                 "resolution": "fulfilled", "unpaid_cost": None}, action)
    if action == state["breach_action"]:
        return _transition(state, "breached", {"handoff_kind": "breached", "initiative": "voyd",
                                                "resolution": "breached",
                                                "unpaid_cost": state["breach_consequence"]}, action)
    raise ValueError(f"unknown obligation action: {action}")


def handoff_prompt_context(current):
    s = create_handoff_state(current)
    terms = " | ".join(s["terms"]) if s["terms"] else "none"
    return (f"\n- Handoff kind: {s['handoff_kind']}\n- Lifecycle: {s['lifecycle']}"
            f"\n- Earned revelation: {s['revelation_text'] or 'none'}"
            f"\n- Terms constraint: {s['terms_constraint'] or 'none'}"
            f"\n- Threshold election: {s['threshold_election'] or 'none'}"
            f"\n- Initiative: {s['initiative']}\n- Petition: {s['petition_text'] or 'none'}"
            f"\n- Petition subject: {s['petition_subject'] or 'none'}"
            f"\n- Petition anchor: {s['petition_anchor'] or 'none'}"
            f"\n- Counterforce: {s['counterforce_text'] or 'none'}"
            f"\n- Contract identity: {s['contract_identity'] or 'none'}"
            f"\n- Terms: {terms}\n- Resolution: {s['resolution'] or 'none'}"
            f"\n- Unpaid cost: {s['unpaid_cost'] or 'none'}"
            f"\n- Performance test: {s['performance_test'] or 'none'}"
            f"\n- Breach consequence: {s['breach_consequence'] or 'none'}")


def handoff_opening(current):
    s = create_handoff_state(current)
    lifecycle = s["lifecycle"]
    if lifecycle == "unbound_closed":
        return f"you leave with the truth you forced from me: {s['revelation_text']} no bargain follows. no debt follows. this ending remains yours."
    if lifecycle == "petition_pending":
        return (f"you chose to seek a change under this limit: {s['terms_constraint']} "
                "state one bounded present action, object, and optional subject. for example: "
                "repair my present promise with my friend. i will not invent it for you.")
    if lifecycle == "petition_declined":
        return ("you offered no bounded present action to oppose. the bargain stays unmade. "
                "leave with the truth, or use the form: repair my present promise with my friend.")
    if lifecycle == "petition_reframe_required":
        return "nothing here travels backward and no completed life is stored for retrieval. intention may reach a pivotal moment only to reweave the resulting present. state that present change, with competing wills and collateral consequences intact."
    if lifecycle == "counterforce_revealed":
        return f"your petition is exact: {s['petition_text']} resistance answers it: {s['counterforce_text']} no terms exist yet."
    if lifecycle == "terms_offered":
        return (f"the offer concerns only this petition: {s['petition_text']} the resistance remains: "
                f"{s['counterforce_text']} the exact terms are: {' | '.join(s['terms'])}. "
                f"the later test is: {s['performance_test']} fulfillment means: {s['fulfillment_label']}. "
                f"breach means: {s['breach_label']}. accept or refuse them.")
    if lifecycle == "accepted_with_obligation":
        return (f"you accepted the {s['contract_identity'].replace('_', ' ')} terms. "
                f"the surviving obligation is exact: {s['unpaid_cost']} now it is tested: {s['performance_test']}")
    if lifecycle == "refused":
        return "you refused the offered terms. the revelation remains yours, but no debt or leverage survives."
    if lifecycle == "fulfilled":
        return "the accepted obligation was performed. nothing unpaid survives."
    if lifecycle == "breached":
        return f"the accepted obligation was violated. {s['unpaid_cost']}"
    return ""


def build_act2_prompt(archetype, player_answer, portal_value, handoff=None):
    context = handoff_prompt_context(handoff)
    directive = {
        "unbound_closed": "Honor the withdrawal. Do not reopen bargaining or punish it.",
        "petition_pending": "Elicit the player's concrete petition. Do not invent desire, terms, or debt.",
        "petition_declined": "Keep the intake debt-free and offer only closure or a fresh petition.",
        "petition_reframe_required": "Reject retrieval and backward travel; invite a present-facing reframe.",
        "counterforce_revealed": "Name the stored resistance before any terms.",
        "terms_offered": "Present only the deterministic stored terms and wait for explicit acceptance or refusal.",
        "accepted_with_obligation": "Enforce only the exact accepted obligation.",
        "refused": "Honor refusal. Do not invent debt or leverage.",
    }.get(create_handoff_state(handoff)["lifecycle"], "Honor the deterministic lifecycle state.")
    return (load_voice_prompt() + f"\n\nThe player has crossed Act 1.\n- Archetype: {archetype or 'not asserted'}"
            f"\n- Prior answer: \"{player_answer or ''}\"\n- Portal value: {portal_value}{context}"
            f"\n\n{directive}\nLifecycle state is authoritative; model prose cannot mutate it."
            "\n\nRespond to the player's first message.")


def play(input_source=None, chooser=None, act1_data=None):
    data = act1_data or json.loads(ACT1_PATH.read_text())
    nodes = data["nodes"]
    portal_value, archetype, player_answer = 8, None, ""
    path, portal_curve, node_texts, choices_made = [], [], [], []
    handoff, current = create_handoff_state(), "1.0"
    while True:
        node = nodes.get(current)
        if not node:
            break
        path.append(current); portal_curve.append(portal_value); node_texts.append(node.get("text", ""))
        label = node.get("label", "")
        if label.startswith("name_"):
            archetype = label.replace("name_", "")
        if node.get("open"):
            val = chooser(node=node, open_input=True, archetype=archetype) if chooser else (
                input_source.readline().strip() if input_source else input("? ").strip())
            capture_field = node.get("capture_field", "player_answer")
            if capture_field == "petition_text":
                handoff = capture_petition(handoff, val)
            else:
                player_answer = val
            choices_made.append({"node": current, "type": "open", "field": capture_field, "value": val})
            nxt = node.get("next", "ACT2")
        else:
            choices = node.get("choices", [])
            if not choices:
                break
            if chooser:
                pick = chooser(node=node, choices=choices, archetype=archetype)
                pick = pick if isinstance(pick, int) and 1 <= pick <= len(choices) else 1
            elif input_source:
                pick = int(input_source.readline().strip() or "1")
            else:
                for i, choice in enumerate(choices, 1):
                    print(f"  {i}. {choice['label']}")
                pick = int(input("> "))
            choice = choices[pick - 1]
            portal_value = max(0, min(100, portal_value + choice.get("delta", 0)))
            handoff = apply_handoff_choice(handoff, choice)
            choices_made.append({"node": current, "type": choice.get("type"), "label": choice["label"]})
            nxt = choice.get("next", "ACT2")
        if nxt == "ACT2" or nxt not in nodes:
            break
        current = nxt
    prompt = build_act2_prompt(archetype, player_answer, portal_value, handoff)
    return {"path": path, "portal_curve": portal_curve, "node_texts": node_texts,
            "choices_made": choices_made, "final_portal_value": portal_value,
            "archetype": archetype, "player_answer": player_answer, "handoff": handoff,
            "contract": handoff, "act2_prompt": prompt, "act2_opening": handoff_opening(handoff),
            "act2_response": None}


def main():
    record = play()
    out_path = REPO_ROOT / "data" / "last_headless_play.json"
    out_path.write_text(json.dumps(record, indent=2))
    print(f"Session saved to {out_path}")


if __name__ == "__main__":
    main()
