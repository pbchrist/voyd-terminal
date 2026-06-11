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
    this.voicePrompt = data.voice_prompt || 'You are the Voyd. Speak in short, lowercase, declarative sentences. Maximum 4-5 sentences per response.';
    this.backendMode = options.backendMode || false;
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
    const trimmed = lower.trim();
    if (trimmed.length < 3) return { intent: 'silence', topic: 'general' };

    // Best topic from keywords (default 'general')
    let bestTopic = 'general';
    let bestScore = 0;
    for (const [topic, keywords] of Object.entries(this.intentMap.keywords)) {
      let score = 0;
      for (const kw of keywords) {
        if (lower.includes(kw)) score++;
      }
      if (score > bestScore) { bestScore = score; bestTopic = topic; }
    }

    // Questions are inquiries, regardless of emotional markers
    const inquiryWords = ['who', 'what', 'where', 'when', 'why', 'how', 'tell', 'explain'];
    if (inquiryWords.some(w => trimmed.startsWith(w))) {
      return { intent: 'inquiry', topic: bestTopic };
    }

    // Emotional markers map to intents; topic stays a keyword topic
    for (const [emotion, markers] of Object.entries(this.intentMap.emotional_markers)) {
      if (markers.some(m => lower.includes(m))) {
        if (emotion === 'defiance') return { intent: 'challenge', topic: bestTopic };
        if (emotion === 'curiosity') return { intent: 'inquiry', topic: bestTopic };
        return { intent: 'confession', topic: bestTopic };
      }
    }

    if (['no', 'never', "won't", "can't", 'hate', 'fight', 'kill', 'destroy'].some(w => lower.includes(w))) {
      return { intent: 'challenge', topic: bestTopic };
    }
    if (['sorry', 'help', 'forgive', 'lost', 'afraid', 'love', 'grief', 'sad'].some(w => lower.includes(w))) {
      return { intent: 'confession', topic: bestTopic };
    }
    return { intent: 'inquiry', topic: bestTopic };
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
    // Conditions are ORs of ANDs of simple clauses. No eval.
    if (condition === 'always') return true;
    const s = this.state;
    const evalClause = (clause) => {
      clause = clause.trim();
      let m;
      if ((m = clause.match(/^intent == '(\w+)'$/))) return intent === m[1];
      if ((m = clause.match(/^topic == '(\w+)'$/))) return topic === m[1];
      if ((m = clause.match(/^depth >= (\d+)$/))) return s.depth >= parseInt(m[1], 10);
      if ((m = clause.match(/^emotional_vector\.(\w+) > ([\d.]+)$/))) return (s.emotion[m[1]] || 0) > parseFloat(m[2]);
      return false;
    };
    return condition.split('||').some(group => group.split('&&').every(evalClause));
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
      const own = this.loreMap[t];
      const chunks = (own && own.length) ? own : (this.loreMap['general'] || []);
      for (const c of chunks) {
        if (!results.includes(c)) results.push(c);
      }
    }
    return results.slice(0, 3);
  }

  buildSystemPrompt(node, loreChunks) {
    // Single source of truth: data/voyd_system.md, embedded at build time.
    const base = this.voicePrompt;

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

  _terminalResult(message) {
    // Always return the full result shape so callers can rely on .state etc.
    return {
      systemPrompt: '',
      contentTemplate: message,
      voydState: 'dissolving',
      nodeType: 'terminus',
      nodeId: this.state.currentNode,
      loreContext: [],
      state: this.exportState(),
      terminated: true,
      intent: 'silence',
      topic: 'general',
    };
  }

  processTurn(playerText) {
    if (this.state.terminated) {
      return this._terminalResult('the dream has ended. there is no returning to a finished dream.');
    }

    const { intent, topic } = this.classifyIntent(playerText);
    this.updateEmotion(intent);

    const nextNodeId = this.selectTransition(intent, topic);
    if (!nextNodeId) {
      this.state.terminated = true;
      this.state.glyphSeed = this.state.glyphSeed || 'voyd';
      return this._terminalResult('the dream dissolves. there is nothing more to say.');
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

    let loreChunks = [];
    if (!this.backendMode) {
      loreChunks = this.getLoreChunks(node.lore_context || []);
    }
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
