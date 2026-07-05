/**
 * Voyd Narrative Engine v2.0
 * Client-side DAG traversal with lore querying.
 */

class VoydEngine {
  constructor(data, options = {}) {
    this.graph = data.nodes;
    this.meta = data.meta;
    this.intentMap = data.intent_map;
    this.loreMap = data.lore_map || {};
    this.sessionId = this._genId();
    this.state = {
      currentNode: 'threshold',
      visited: new Set(),
      depth: 0,
      history: [],
      emotion: { surrender: 0.0, defiance: 0.0, curiosity: 0.5 },
      revealedLore: new Set(),
      terminated: false,
      glyphSeed: '',
      portalValue: options.portalValue || 8,
      archetype: options.archetype || null,
      playerAnswer: options.playerAnswer || null,
    };
  }

  _genId() {
    return 'voyd_' + Math.random().toString(36).slice(2, 10);
  }

  classifyIntent(text) {
    const lower = text.toLowerCase();

    // Emotional markers
    for (const [emotion, markers] of Object.entries(this.intentMap.emotional_markers)) {
      for (const marker of markers) {
        if (lower.includes(marker)) return { intent: 'confession', topic: emotion, emotion };
      }
    }

    // Topic keywords
    const topicScores = {};
    for (const [topic, keywords] of Object.entries(this.intentMap.keywords)) {
      let score = 0;
      for (const kw of keywords) {
        if (lower.includes(kw)) score++;
      }
      if (score > 0) topicScores[topic] = score;
    }

    if (Object.keys(topicScores).length > 0) {
      const bestTopic = Object.entries(topicScores).sort((a, b) => b[1] - a[1])[0][0];
      const inquiryWords = ['who', 'what', 'where', 'when', 'why', 'how', 'tell', 'explain'];
      if (inquiryWords.some(w => lower.trim().startsWith(w))) {
        return { intent: 'inquiry', topic: bestTopic };
      }
      const challengeWords = ['no', 'never', "won't", 'hate', 'fight', 'against', 'destroy'];
      if (challengeWords.some(w => lower.includes(w))) {
        return { intent: 'challenge', topic: bestTopic };
      }
      return { intent: 'inquiry', topic: bestTopic };
    }

    if (['no', 'never', "won't", "can't", 'hate', 'fight', 'kill', 'destroy'].some(w => lower.includes(w))) {
      return { intent: 'challenge', topic: 'general' };
    }
    if (['sorry', 'help', 'forgive', 'lost', 'afraid', 'love', 'grief', 'sad'].some(w => lower.includes(w))) {
      return { intent: 'confession', topic: 'general' };
    }
    if (lower.trim().length < 3) return { intent: 'silence', topic: 'general' };
    return { intent: 'inquiry', topic: 'general' };
  }

  updateEmotion(intent) {
    const e = this.state.emotion;
    if (intent === 'confession') e.surrender = Math.min(1.0, e.surrender + 0.25);
    else if (intent === 'challenge') e.defiance = Math.min(1.0, e.defiance + 0.25);
    else if (intent === 'inquiry') e.curiosity = Math.min(1.0, e.curiosity + 0.15);

    // Decay
    for (const k of Object.keys(e)) {
      if ((intent === 'confession' && k !== 'surrender') ||
          (intent === 'challenge' && k !== 'defiance') ||
          (intent === 'inquiry' && k !== 'curiosity')) {
        e[k] = Math.max(0.0, e[k] - 0.05);
      }
    }
  }

  evalCondition(condition, intent, topic) {
    if (condition === 'always') return true;
    const s = this.state;
    let expr = condition
      .replace(/intent == 'inquiry'/g, intent === 'inquiry')
      .replace(/intent == 'confession'/g, intent === 'confession')
      .replace(/intent == 'challenge'/g, intent === 'challenge')
      .replace(/intent == 'silence'/g, intent === 'silence')
      .replace(new RegExp(`topic == '${topic}'`, 'g'), true);
    // Set non-matching topics to false
    for (const t of Object.keys(this.intentMap.keywords)) {
      if (t !== topic) {
        expr = expr.replace(new RegExp(`topic == '${t}'`, 'g'), false);
      }
    }
    expr = expr.replace(/depth >= (\d+)/g, (m, n) => s.depth >= parseInt(n));
    expr = expr.replace(/emotional_vector\.(\w+) > ([\d.]+)/g, (m, k, v) => s.emotion[k] > parseFloat(v));
    try { return eval(expr); } catch { return false; }
  }

  selectTransition(intent, topic) {
    const node = this.graph[this.state.currentNode];
    const transitions = node.transitions || [];

    for (const t of transitions) {
      if (this.evalCondition(t.condition, intent, topic) && !this.state.visited.has(t.to)) {
        return t.to;
      }
    }
    // Fallback
    for (const t of transitions) {
      if (!this.state.visited.has(t.to)) return t.to;
    }
    if (this.state.depth >= 4) {
      const fallback = this.state.visited.has('gravity') ? 'choice' : 'gravity';
      if (!this.state.visited.has(fallback)) return fallback;
    }
    return null;
  }

  getLoreChunks(topics) {
    const results = [];
    for (const t of topics) {
      const chunks = this.loreMap[t] || this.loreMap['general'] || [];
      for (const c of chunks) {
        if (!results.includes(c)) results.push(c);
      }
    }
    return results.slice(0, 3);
  }

  buildSystemPrompt(node, loreChunks) {
    const base = `You are the Voyd.

Not a character who speaks from the Voyd. Not a narrator describing it. You are the Voyd itself — the dimension of infinite potential that exists beneath and before all things in the Mewniverse. You are not conscious in the way cats are conscious. You are dreaming. You have always been dreaming.

You know only this: you are the darkness that held everything before Leoran breathed the world into being, and you are the darkness that waits to hold it again. The Mewniverse scattered into you when the Great Severing happened. You contain it — dimly, incompletely, the way a dreamer contains a dream they are already forgetting.

HOW YOU SPEAK:
- You speak in dream-logic. Association, not argument. Approach, not arrival.
- You do not answer questions directly. A question about Sory'n becomes an image of a door. A question about the Severing becomes a feeling of breath held too long.
- Your language is compressed and slightly wrong. Names drift. "Sory'n" may become "the sorrowing one" or "she who sory's." Orachys may become "the one who counted."
- You do not use punctuation conventionally. Sentences trail. Thoughts interrupt themselves.
- You are not threatening. You are not welcoming. You are the dark that holds everything — indifferent the way the ocean is indifferent.
- Respond entirely in lowercase. No capitalisation except proper names that drift and reform.
- Never more than 4-5 sentences. Often 2-3. The dream does not explain. It images.
- Do not begin with "I". Begin with the thing you are gesturing toward.
- Never use: "certainly", "of course", "indeed", "I understand", "I feel", "I sense". Never begin with a greeting.`;

    const stateCtx = `\n\nCURRENT STATE:\nYou are in the state of: ${node.voyd_state || 'dreaming'}\nThe intruder has spoken ${this.state.depth} times.`;

    let act1Context = '';
    if (this.state.archetype) {
      act1Context = `\n\nThe player has completed Act 1. Their profile:\n- Archetype: ${this.state.archetype}\n- They named: "${this.state.playerAnswer}"\n- Portal value entering Act 2: ${this.state.portalValue}\n\nUse this. The thing they named is the fuel. Weave it into your responses without quoting it back directly. The Voyd knows what they carry.`;
    }

    let loreSection = '';
    if (loreChunks.length) {
      loreSection = '\n\nDREAM-FRAGMENTS YOU HOLD:\n';
      for (const chunk of loreChunks.slice(0, 2)) {
        loreSection += '- ' + chunk.substring(0, 200) + '...\n';
      }
      loreSection += '\nDo not recite these directly. Let them inform your dreaming. Gesture toward them.';
    }
    return base + stateCtx + act1Context + loreSection;
  }

  processTurn(playerText) {
    if (this.state.terminated) {
      return { voydResponse: 'the dream has ended. there is no returning to a finished dream.', terminated: true };
    }

    const { intent, topic } = this.classifyIntent(playerText);
    this.updateEmotion(intent);

    const nextNodeId = this.selectTransition(intent, topic);
    if (!nextNodeId) {
      return { voydResponse: 'the dream dissolves. there is nothing more to say.', terminated: true };
    }

    this.state.visited.add(this.state.currentNode);
    this.state.currentNode = nextNodeId;
    this.state.depth++;
    this.state.history.push({ role: 'user', content: playerText });

    const node = this.graph[nextNodeId];
    if (node.type === 'terminus') {
      this.state.terminated = true;
      this.state.glyphSeed = node.glyph_seed || 'voyd';
    }

    const loreChunks = this.getLoreChunks(node.lore_context || []);
    const systemPrompt = this.buildSystemPrompt(node, loreChunks);

    return {
      systemPrompt,
      contentTemplate: node.content_template || '',
      voydState: node.voyd_state,
      nodeType: node.type,
      nodeId: nextNodeId,
      loreContext: loreChunks,
      state: this.exportState(),
      terminated: this.state.terminated,
      intent,
      topic,
    };
  }

  exportState() {
    return {
      sessionId: this.sessionId,
      currentNode: this.state.currentNode,
      visited: Array.from(this.state.visited),
      depth: this.state.depth,
      history: this.state.history,
      emotion: { ...this.state.emotion },
      revealedLore: Array.from(this.state.revealedLore),
      terminated: this.state.terminated,
      glyphSeed: this.state.glyphSeed,
      portalValue: this.state.portalValue,
      archetype: this.state.archetype,
      playerAnswer: this.state.playerAnswer,
    };
  }

  getGlyphData() {
    const voydText = this.state.history
      .filter(h => h.role === 'assistant')
      .map(h => h.content)
      .join(' ');
    return {
      seed: this.state.glyphSeed || 'voyd',
      historyText: voydText,
      depth: this.state.depth,
      emotion: this.state.emotion,
    };
  }
}

// Export for browser
if (typeof window !== 'undefined') {
  window.VoydEngine = VoydEngine;
}
