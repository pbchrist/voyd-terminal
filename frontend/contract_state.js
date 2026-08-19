(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  root.VoydContracts = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const CONTRACT_FIELDS = [
    'identity', 'terms', 'initiative', 'resolution', 'unpaid_cost',
    'choice_history', 'personal_referent', 'exposed_risk',
    'reciprocal_demand', 'explicit_test'
  ];

  function createContractState(seed) {
    const base = {
      identity: null,
      terms: [],
      initiative: 'player',
      resolution: 'unformed',
      unpaid_cost: null,
      choice_history: [],
      personal_referent: null,
      exposed_risk: null,
      reciprocal_demand: null,
      explicit_test: null,
    };
    const source = seed || {};
    for (const field of CONTRACT_FIELDS) {
      if (Object.prototype.hasOwnProperty.call(source, field)) {
        base[field] = Array.isArray(source[field]) ? source[field].slice() : source[field];
      }
    }
    return base;
  }

  function applyContractChoice(current, choice) {
    let next = createContractState(current);
    if (choice && choice.contract_start) next = createContractState(choice.contract_start);
    if (choice && choice.contract_update) {
      for (const field of CONTRACT_FIELDS) {
        if (field === 'choice_history') continue;
        if (Object.prototype.hasOwnProperty.call(choice.contract_update, field)) {
          const value = choice.contract_update[field];
          next[field] = Array.isArray(value) ? value.slice() : value;
        }
      }
    }
    if (choice && choice.contract_action) next.choice_history.push(choice.contract_action);
    return next;
  }

  function contractPromptContext(contract) {
    const c = createContractState(contract);
    if (!c.identity) return '';
    const terms = c.terms.length ? c.terms.join(' | ') : 'none';
    const history = c.choice_history.length ? c.choice_history.join(' -> ') : 'none';
    return `\n- Active contract: ${c.identity}` +
      `\n- Contract terms: ${terms}` +
      `\n- Initiative: ${c.initiative}` +
      `\n- Resolution: ${c.resolution}` +
      `\n- Unpaid cost: ${c.unpaid_cost || 'none'}` +
      `\n- Choice history: ${history}` +
      `\n- Personal referent: ${c.personal_referent || 'undisclosed'}` +
      `\n- Voyd risk exposed: ${c.exposed_risk || 'none'}` +
      `\n- Reciprocal demand: ${c.reciprocal_demand || 'none'}` +
      `\n- Test already performed: ${c.explicit_test || 'none'}`;
  }

  function contractOpening(contract) {
    const c = createContractState(contract);
    if (!c.identity) return '';
    const name = c.identity.replace(/_/g, ' ');
    const subject = c.personal_referent || 'chosen subject';
    if (c.unpaid_cost) {
      return `the ${name} contract enters before your question. it ended ${c.resolution}, with ${c.initiative} holding initiative over ${subject}. the unpaid cost is still exact: ${c.unpaid_cost}. answer from inside that consequence.`;
    }
    return `the ${name} contract enters before your question. it ended ${c.resolution}, with ${c.initiative} holding initiative over ${subject}. nothing unpaid survives, so i will not invent a new debt. answer from the consequence you chose.`;
  }

  return { CONTRACT_FIELDS, createContractState, applyContractChoice, contractPromptContext, contractOpening };
});
