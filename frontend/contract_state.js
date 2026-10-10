(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.VoydContracts = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const HANDOFF_FIELDS = [
    'handoff_kind', 'revelation_id', 'revelation_text', 'terms_constraint',
    'threshold_election', 'lifecycle', 'petition_text', 'petition_subject', 'petition_object', 'petition_action',
    'petition_anchor', 'petition_status', 'counterforce_id', 'counterforce_text',
    'contract_identity', 'terms', 'initiative', 'resolution', 'unpaid_cost',
    'performance_test', 'fulfillment_action', 'fulfillment_label', 'breach_action',
    'breach_label', 'breach_consequence', 'choice_history'
  ];

  const REVELATIONS = {
    demanded_identity: {
      revelation_id: 'release_starves_intention',
      revelation_text: 'intention gives the Voyd purchase on the unfinished present, while genuine release starves that purchase.',
      terms_constraint: 'any offer must preserve genuine release as an available end to the Voyd\'s pressure and cannot promise retrieval.'
    },
    claimed_knowledge: {
      revelation_id: 'reweaving_is_not_retrieval',
      revelation_text: 'the Voyd stores no completed life or earlier self; intention may reach a pivotal moment only to reweave the resulting present amid competing wills and collateral change.',
      terms_constraint: 'any offer must name forward reweaving of the present, never backward travel, retrieval, or a stored life.'
    },
    demanded_motive: {
      revelation_id: 'intention_is_the_appetite',
      revelation_text: 'the Voyd recruits sustained intention because a living plan feeds it, but it cannot erase competing wills or collateral consequences.',
      terms_constraint: 'any offer may apply one bounded pressure to the unfinished present and must leave competing wills and consequences intact.'
    },
    identity_as_bait: {
      revelation_id: 'possibility_is_a_lure',
      revelation_text: 'the identity called possibility is a recruiting lure: its image is proposed, not a person or outcome stored for recovery.',
      terms_constraint: 'any offer must identify the image as a proposed future and may grant only one disclosed, bounded use of that lure.'
    }
  };

  const COUNTERFORCES = {
    demanded_identity: ['competing_will', 'the will touched by the requested change can refuse the direction placed upon it.'],
    claimed_knowledge: ['collateral_consequences', 'reweaving the present preserves every competing will and changes consequences beyond the requested result.'],
    demanded_motive: ['existing_obligation', 'the requested change collides with an obligation already active in the present and cannot erase it.'],
    identity_as_bait: ['required_sacrifice', 'to pursue the proposed image, the player must release the comforting belief that the desired outcome already exists somewhere to be recovered.']
  };

  const OFFERS = {
    demanded_identity: {
      terms: ['apply one bounded pressure toward the stated petition', 'the affected will remains free to refuse', 'genuine release ends the Voyd\'s leverage'],
      cost: 'the Voyd may press the stated petition once, until the player genuinely releases that direction'
    },
    claimed_knowledge: {
      terms: ['reweave only the present consequences named in the petition', 'no backward travel or stored life is promised', 'collateral consequences remain real'],
      cost: 'the player must answer for the collateral consequence revealed beside the petition'
    },
    demanded_motive: {
      terms: ['authorize one bounded pressure toward the stated petition', 'the existing obligation and competing wills remain', 'no past event is returned'],
      cost: 'one authorized pressure toward the petition remains to be answered for'
    },
    identity_as_bait: {
      terms: ['treat the desired image as a proposed future, never a stored outcome', 'authorize one disclosed use of that image as leverage', 'the image expires after that use'],
      cost: 'the disclosed proposed image may be used once as leverage and no more'
    }
  };

  const OBLIGATION_TESTS = {
    demanded_identity: {
      test: '{subject} refuses the directed change to {object} inside "{petition}". {counterforce} release that direction now, or continue it knowingly.',
      fulfillment_action: 'release_directed_pressure', fulfillment_label: 'release my direction to {action} {subject}\'s {object}',
      breach_action: 'continue_directed_pressure', breach_label: 'continue directing the action {action} over {subject}\'s {object}',
      breach_consequence: 'the Voyd may use the continued action {action} over {subject}\'s {object} once as leverage until it is genuinely released'
    },
    claimed_knowledge: {
      test: '{subject} invokes the disclosed right to treat {object} as void after "{petition}" reweaves it. {counterforce} acknowledge that loss of enforceability, or deny it by calling the reweaving retrieval.',
      fulfillment_action: 'acknowledge_collateral_consequence', fulfillment_label: 'acknowledge {subject}\'s right to treat the action {action} on {object} as void',
      breach_action: 'misname_change_as_retrieval', breach_label: 'deny {subject}\'s right over the action {action} on {object} and call it retrieval',
      breach_consequence: 'the Voyd holds denial of {subject}\'s disclosed right over the action {action} on {object} as leverage'
    },
    demanded_motive: {
      test: '{subject} refuses pressure on {object} before "{petition}" can proceed. {counterforce} preserve that refusal, or discard it to preserve the desired result.',
      fulfillment_action: 'honor_existing_obligation', fulfillment_label: 'preserve {subject}\'s refusal of the action {action} on {object}',
      breach_action: 'discard_existing_obligation', breach_label: 'discard {subject}\'s refusal of the action {action} on {object}',
      breach_consequence: 'the Voyd may collect pressure through the discarded refusal of the action {action} over {subject}\'s {object}'
    },
    identity_as_bait: {
      test: 'the proposed image of changed {subject}\'s {object} behind "{petition}" now claims it was waiting here all along. {counterforce} release that false claim, or declare the image stored.',
      fulfillment_action: 'release_stored_outcome_belief', fulfillment_label: 'release the claim that the action {action} on {subject}\'s {object} was stored',
      breach_action: 'claim_outcome_was_stored', breach_label: 'claim the image created by {action} on {subject}\'s {object} was stored',
      breach_consequence: 'the Voyd may use the falsely stored image created by {action} on {subject}\'s {object} once as leverage'
    }
  };

  const LEGAL = {
    revelation_only: ['unbound_closed', 'petition_pending'],
    petition_pending: ['petition_declined', 'petition_reframe_required', 'petition_validated'],
    petition_reframe_required: ['petition_declined', 'petition_reframe_required', 'petition_validated'],
    petition_declined: ['petition_pending', 'unbound_closed'],
    petition_validated: ['counterforce_revealed'],
    counterforce_revealed: ['terms_offered'],
    terms_offered: ['refused', 'accepted_with_obligation'],
    accepted_with_obligation: ['fulfilled', 'breached'],
    unbound_closed: [], refused: [], fulfilled: [], breached: []
  };

  const ACTION_OBJECTS = {
    relationship: ['repair', 'rebuild', 'reconcile', 'release', 'end', 'protect', 'mend', 'break'],
    promise: ['repair', 'release', 'end', 'protect', 'break', 'commit', 'keep', 'honor', 'maintain', 'fulfill'],
    obligation: ['change', 'alter', 'release', 'end', 'protect', 'confront', 'commit'],
    consequence: ['change', 'alter', 'reweave', 'confront', 'prevent'],
    course: ['change', 'alter', 'reweave'],
    bond: ['repair', 'rebuild', 'reconcile', 'release', 'end', 'protect', 'mend', 'break'],
    self: ['change', 'alter', 'rebuild'], life: ['alter', 'rebuild', 'protect'],
    decision: ['change', 'alter', 'reweave', 'confront'],
    work: ['change', 'alter', 'rebuild', 'protect', 'end'],
    home: ['repair', 'rebuild', 'protect', 'leave'],
    habit: ['change', 'alter', 'end', 'stop', 'start', 'break'],
    fear: ['confront', 'release', 'end'], grief: ['confront', 'release'],
    claim: ['release', 'end', 'protect', 'break'],
    direction: ['change', 'alter', 'release', 'end', 'protect'],
    commitment: ['start', 'end', 'protect', 'break', 'commit']
  };

  function createHandoffState(seed) {
    const base = {
      handoff_kind: 'revelation_only', revelation_id: null, revelation_text: null,
      terms_constraint: null, threshold_election: null, lifecycle: 'revelation_only',
      petition_text: null, petition_subject: null, petition_object: null, petition_action: null, petition_anchor: null,
      petition_status: null, counterforce_id: null, counterforce_text: null,
      contract_identity: null, terms: [], initiative: 'player', resolution: null,
      unpaid_cost: null, performance_test: null, fulfillment_action: null,
      fulfillment_label: null, breach_action: null, breach_label: null,
      breach_consequence: null, choice_history: []
    };
    const source = seed || {};
    for (const field of HANDOFF_FIELDS) {
      if (Object.prototype.hasOwnProperty.call(source, field)) {
        base[field] = Array.isArray(source[field]) ? source[field].slice() : source[field];
      }
    }
    const preTerms = ['revelation_only', 'unbound_closed', 'petition_pending',
      'petition_declined', 'petition_reframe_required', 'petition_validated',
      'counterforce_revealed'];
    if (preTerms.includes(base.lifecycle)) {
      base.contract_identity = null; base.terms = []; base.unpaid_cost = null;
      base.performance_test = null; base.fulfillment_action = null; base.fulfillment_label = null;
      base.breach_action = null; base.breach_label = null; base.breach_consequence = null;
    } else if (['terms_offered', 'refused', 'fulfilled'].includes(base.lifecycle)) {
      base.unpaid_cost = null;
    }
    return base;
  }

  function revelationState(route) {
    if (!REVELATIONS[route]) throw new Error(`unknown revelation route: ${route}`);
    return createHandoffState(Object.assign({
      handoff_kind: 'revelation_only', lifecycle: 'revelation_only', initiative: 'player'
    }, REVELATIONS[route]));
  }

  function transition(current, lifecycle, update, action) {
    const state = createHandoffState(current);
    const allowed = LEGAL[state.lifecycle] || [];
    if (!allowed.includes(lifecycle)) throw new Error(`illegal lifecycle transition: ${state.lifecycle} -> ${lifecycle}`);
    state.lifecycle = lifecycle;
    Object.assign(state, update || {});
    if (action) state.choice_history.push(action);
    return createHandoffState(state);
  }

  function applyHandoffChoice(current, choice) {
    let state = choice && choice.handoff_start ? createHandoffState(choice.handoff_start) : createHandoffState(current);
    if (choice && choice.handoff_update) {
      const target = choice.handoff_update.lifecycle;
      if (target && target !== state.lifecycle) {
        const update = Object.assign({}, choice.handoff_update); delete update.lifecycle;
        return transition(state, target, update, choice.handoff_action);
      }
      Object.assign(state, choice.handoff_update);
    }
    if (choice && choice.handoff_action) state.choice_history.push(choice.handoff_action);
    return createHandoffState(state);
  }

  function applyHandoffAction(current, action) {
    if (action === 'withdraw') return transition(current, 'unbound_closed', {
      handoff_kind: 'unbound_closed', threshold_election: 'withdraw', initiative: 'player',
      resolution: null, contract_identity: null, terms: [], unpaid_cost: null
    }, 'withdraw_with_truth');
    if (action === 'seek_change') return transition(current, 'petition_pending', {
      handoff_kind: 'petition_pending', threshold_election: 'seek_change', initiative: 'player',
      resolution: null, contract_identity: null, terms: [], unpaid_cost: null
    }, 'seek_concrete_change');
    if (action === 'reopen_petition') return transition(current, 'petition_pending', {
      handoff_kind: 'petition_pending', petition_status: null
    }, 'state_change_after_declining');
    if (action === 'close_unbound') return transition(current, 'unbound_closed', {
      handoff_kind: 'unbound_closed', initiative: 'player'
    }, 'close_without_bargain');
    throw new Error(`unknown handoff action: ${action}`);
  }

  function capturePetition(current, text) {
    const state = createHandoffState(current);
    if (!['petition_pending', 'petition_reframe_required'].includes(state.lifecycle)) {
      throw new Error(`petition cannot be captured from ${state.lifecycle}`);
    }
    const raw = String(text || '').trim();
    const lower = raw.toLowerCase();
    const words = lower.match(/[a-z']+/g) || [];
    const petitionMatch = lower.match(/^(?:please\s+)?(?:i\s+(?:want|need|choose|intend|seek|ask)\s+to\s+)?(change|alter|reweave|repair|rebuild|reconcile|release|end|stop|start|begin|become|leave|protect|break|commit|keep|honor|maintain|fulfill|forgive|apologize|confront|prevent|save|free|move|finish|mend|press)\s+(?:my|the|a)\s+(?:present\s+)?(relationship|promise|obligation|consequence|course|bond|self|life|decision|work|home|habit|fear|grief|claim|direction|commitment)(?:\s+(?:with|about|toward|for)\s+(myself|another person|my family|my friend|my partner))?[.!?]*$/);
    const petitionObject = petitionMatch ? petitionMatch[2] : null;
    const petitionAction = petitionMatch ? petitionMatch[1] : null;
    const compatible = petitionObject && petitionAction && ACTION_OBJECTS[petitionObject].includes(petitionAction);
    const personMarker = /\b(mother|father|brother|sister|wife|husband|person|friend|she|he|her|him|someone|anyone)\b/.test(lower);
    const deathMarker = /\b(dead|death|died|dying|gone|deceased|late|killed|murdered|murder|killing|passing|passed away|buried|lost|life|alive|breathe|live again)\b/.test(lower);
    const restoreMarker = /\b(resurrect\w*|reviv\w*|restor\w*|recover\w*|bring\w*|brought|make\w*|raise\w*|undo\w*|reverse\w*|save\w*|return\w*)\b/.test(lower);
    const deathReturn = restoreMarker && (personMarker || deathMarker);
    const temporalMarker = /\b(time|past|yesterday|earlier|childhood|previous day|day before|day we met|when .{0,20} alive|last (?:week|month|year)|(?:17|18|19|20)\d{2}|(?:(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:[- ](?:one|two|three|four|five|six|seven|eight|nine))?|\d+) (?:days?|years?|months?|weeks?|decades?|centuries?)|a decade)\b/.test(lower);
    const temporalMove = /\b(rewind\w*|reliv\w*|return\w*|travel\w*|transport\w*|carry\w*|take\w*|go|going|turn\w*|reverse\w*|roll\w*|send\w*|back)\b/.test(lower);
    const timeReturn = temporalMarker && temporalMove;
    const directFalse = /\b(retriev\w*|resurrect\w*|reviv\w*)\b|stored (?:life|person|self)/.test(lower);
    const falseMechanism = !petitionMatch && (deathReturn || timeReturn || directFalse);
    if (falseMechanism) return transition(state, 'petition_reframe_required', {
      handoff_kind: 'petition_reframe_required', petition_text: raw,
      petition_status: 'reframe_required', contract_identity: null, terms: [], unpaid_cost: null,
      initiative: 'player'
    }, 'reject_retrieval_mechanism');
    const evasive = !raw || /^(nothing|never mind|nevermind|i don't know|no change|pass|perhaps|maybe|i would rather not say)[.! ]*$/.test(lower) || words.length < 3 || !petitionMatch || !compatible;
    if (evasive) return transition(state, 'petition_declined', {
      handoff_kind: 'petition_declined', petition_text: raw || null,
      petition_status: 'declined', contract_identity: null, terms: [], unpaid_cost: null,
      initiative: 'player'
    }, 'decline_petition');
    const subject = petitionMatch[3] || 'myself';
    const anchor = /(past|pivotal|moment|consequence|broke|before)/.test(lower) ? 'pivotal_moment' : 'present_condition';
    return transition(state, 'petition_validated', {
      handoff_kind: 'petition_validated', petition_text: raw, petition_subject: subject,
      petition_object: petitionObject, petition_action: petitionAction,
      petition_anchor: anchor, petition_status: 'validated', initiative: 'player',
      contract_identity: null, terms: [], unpaid_cost: null
    }, 'state_concrete_petition');
  }

  function routeFor(state) {
    return Object.keys(REVELATIONS).find(key => REVELATIONS[key].revelation_id === state.revelation_id);
  }

  function revealCounterforce(current) {
    const state = createHandoffState(current);
    if (state.lifecycle !== 'petition_validated' || !state.petition_text) throw new Error('counterforce requires a validated petition');
    const route = routeFor(state); const counter = COUNTERFORCES[route];
    const object = state.petition_object;
    const subject = state.petition_subject;
    const action = state.petition_action;
    const concrete = {
      demanded_identity: `${subject} can refuse the action ${action} applied to ${object}.`,
      claimed_knowledge: `${action} applied through reweaving ${object} grants ${subject} the disclosed right to treat it as void; that loss of enforceability is collateral.`,
      demanded_motive: `${subject} can refuse the action ${action} on ${object}; preserving that refusal limits the Voyd's appetite.`,
      identity_as_bait: `the proposed image created by ${action} on ${subject}'s ${object} must be surrendered if it masquerades as stored.`
    }[route];
    return transition(state, 'counterforce_revealed', {
      handoff_kind: 'counterforce_revealed', counterforce_id: counter[0],
      counterforce_text: `for "${state.petition_text}", ${concrete}`, initiative: 'voyd'
    }, 'counterforce_revealed');
  }

  function offerTerms(current) {
    const state = createHandoffState(current);
    if (state.lifecycle !== 'counterforce_revealed' || !state.petition_text || !state.counterforce_id) {
      throw new Error('terms require a petition-specific counterforce');
    }
    const route = routeFor(state); const offer = OFFERS[route];
    const test = OBLIGATION_TESTS[route];
    const render = value => value.replaceAll('{petition}', state.petition_text)
      .replaceAll('{counterforce}', state.counterforce_text).replaceAll('{object}', state.petition_object)
      .replaceAll('{subject}', state.petition_subject).replaceAll('{action}', state.petition_action);
    const breach = render(test.breach_consequence);
    return transition(state, 'terms_offered', {
      handoff_kind: 'terms_offered', contract_identity: null,
      terms: offer.terms.concat([state.terms_constraint, `the petition action remains ${state.petition_action}; no opposite action may be substituted`, breach]), initiative: 'player',
      resolution: null, unpaid_cost: null, performance_test: render(test.test),
      fulfillment_action: `${test.fulfillment_action}_${state.petition_action}`, fulfillment_label: render(test.fulfillment_label),
      breach_action: `${test.breach_action}_${state.petition_action}`, breach_label: render(test.breach_label),
      breach_consequence: breach
    }, 'hear_constrained_terms');
  }

  function resolveOffer(current, action) {
    const state = createHandoffState(current);
    if (state.lifecycle !== 'terms_offered' || !state.terms.length) throw new Error('an exact offer must exist first');
    const route = routeFor(state);
    if (action === 'refuse') return transition(state, 'refused', {
      handoff_kind: 'refused', initiative: 'player', contract_identity: null,
      resolution: 'refused', unpaid_cost: null
    }, 'refuse_exact_terms');
    if (action === 'accept') {
      return transition(state, 'accepted_with_obligation', {
        handoff_kind: 'accepted_with_obligation', initiative: 'voyd',
        contract_identity: route, resolution: 'accepted_with_obligation',
        unpaid_cost: `${OFFERS[route].cost}: ${state.petition_action} ${state.petition_object} for ${state.petition_subject}`
      }, 'accept_exact_terms');
    }
    throw new Error(`unknown offer action: ${action}`);
  }

  function resolveObligation(current, action) {
    const state = createHandoffState(current);
    if (state.lifecycle !== 'accepted_with_obligation' || !state.unpaid_cost) throw new Error('no accepted obligation to resolve');
    if (action === state.fulfillment_action) return transition(state, 'fulfilled', {
      handoff_kind: 'fulfilled', initiative: 'player', resolution: 'fulfilled', unpaid_cost: null
    }, action);
    if (action === state.breach_action) return transition(state, 'breached', {
      handoff_kind: 'breached', initiative: 'voyd', resolution: 'breached',
      unpaid_cost: state.breach_consequence
    }, action);
    throw new Error(`unknown obligation action: ${action}`);
  }

  function handoffPromptContext(current) {
    const s = createHandoffState(current);
    let out = `\n- Handoff kind: ${s.handoff_kind}\n- Lifecycle: ${s.lifecycle}`;
    out += `\n- Earned revelation: ${s.revelation_text || 'none'}\n- Terms constraint: ${s.terms_constraint || 'none'}`;
    out += `\n- Threshold election: ${s.threshold_election || 'none'}\n- Initiative: ${s.initiative}`;
    out += `\n- Petition: ${s.petition_text || 'none'}\n- Petition subject: ${s.petition_subject || 'none'}\n- Petition anchor: ${s.petition_anchor || 'none'}`;
    out += `\n- Counterforce: ${s.counterforce_text || 'none'}\n- Contract identity: ${s.contract_identity || 'none'}`;
    out += `\n- Terms: ${s.terms.length ? s.terms.join(' | ') : 'none'}\n- Resolution: ${s.resolution || 'none'}\n- Unpaid cost: ${s.unpaid_cost || 'none'}`;
    out += `\n- Performance test: ${s.performance_test || 'none'}\n- Breach consequence: ${s.breach_consequence || 'none'}`;
    return out;
  }

  function handoffOpening(current) {
    const s = createHandoffState(current);
    if (s.lifecycle === 'unbound_closed') return `you leave with the truth you forced from me: ${s.revelation_text} no bargain follows. no debt follows. this ending remains yours.`;
    if (s.lifecycle === 'petition_pending') return `you chose to seek a change under this limit: ${s.terms_constraint} state one bounded present action, object, and optional subject. for example: repair my present promise with my friend. i will not invent it for you.`;
    if (s.lifecycle === 'petition_declined') return `you offered no bounded present action to oppose. the bargain stays unmade. leave with the truth, or use the form: repair my present promise with my friend.`;
    if (s.lifecycle === 'petition_reframe_required') return `nothing here travels backward and no completed life is stored for retrieval. intention may reach a pivotal moment only to reweave the resulting present. state that present change, with competing wills and collateral consequences intact.`;
    if (s.lifecycle === 'counterforce_revealed') return `your petition is exact: ${s.petition_text} resistance answers it: ${s.counterforce_text} no terms exist yet.`;
    if (s.lifecycle === 'terms_offered') return `the offer concerns only this petition: ${s.petition_text} the resistance remains: ${s.counterforce_text} the exact terms are: ${s.terms.join(' | ')}. the later test is: ${s.performance_test} fulfillment means: ${s.fulfillment_label}. breach means: ${s.breach_label}. accept or refuse them.`;
    if (s.lifecycle === 'accepted_with_obligation') return `you accepted the ${s.contract_identity.replace(/_/g, ' ')} terms. the surviving obligation is exact: ${s.unpaid_cost} now it is tested: ${s.performance_test}`;
    if (s.lifecycle === 'refused') return `you refused the offered terms. the revelation remains yours, but no debt or leverage survives.`;
    if (s.lifecycle === 'fulfilled') return `the accepted obligation was performed. nothing unpaid survives.`;
    if (s.lifecycle === 'breached') return `the accepted obligation was violated. ${s.unpaid_cost}`;
    return '';
  }

  return {
    HANDOFF_FIELDS, REVELATIONS, LEGAL, OBLIGATION_TESTS, createHandoffState, revelationState,
    applyHandoffChoice, applyHandoffAction, capturePetition, revealCounterforce,
    offerTerms, resolveOffer, resolveObligation, handoffPromptContext, handoffOpening
  };
});
