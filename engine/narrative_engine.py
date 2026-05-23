"""
Narrative Engine for the Voyd Terminal
Manages DAG traversal, intent classification, emotional state, and response generation.
"""

import json
import random
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict

from .lore_index import get_index

STORY_GRAPH_PATH = Path(__file__).parent.parent / "data" / "story_graph.json"


@dataclass
class SessionState:
    session_id: str
    current_node: str = "threshold"
    visited_nodes: Set[str] = field(default_factory=set)
    depth: int = 0
    history: List[Dict] = field(default_factory=list)
    emotional_vector: Dict[str, float] = field(default_factory=lambda: {
        "surrender": 0.0,
        "defiance": 0.0,
        "curiosity": 0.5,
    })
    revealed_lore: Set[str] = field(default_factory=set)
    phase: str = "threshold"  # threshold, dialogue, terminus
    is_terminated: bool = False
    glyph_seed: str = ""

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "current_node": self.current_node,
            "visited_nodes": list(self.visited_nodes),
            "depth": self.depth,
            "history": self.history,
            "emotional_vector": self.emotional_vector,
            "revealed_lore": list(self.revealed_lore),
            "phase": self.phase,
            "is_terminated": self.is_terminated,
            "glyph_seed": self.glyph_seed,
        }


class NarrativeEngine:
    def __init__(self):
        with open(STORY_GRAPH_PATH) as f:
            data = json.load(f)
        self.graph = data["nodes"]
        self.intent_map = data["intent_map"]
        self.max_depth = data["meta"]["max_depth"]
        self.sessions: Dict[str, SessionState] = {}

    def get_or_create_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id=session_id)
        return self.sessions[session_id]

    def classify_intent(self, text: str) -> Tuple[str, str]:
        """Classify player input into intent and topic."""
        lower = text.lower()

        # Emotional scoring
        for emotion, markers in self.intent_map["emotional_markers"].items():
            for marker in markers:
                if marker in lower:
                    return "confession", emotion

        # Topic keywords
        topic_scores = {}
        for topic, keywords in self.intent_map["keywords"].items():
            score = sum(1 for kw in keywords if kw in lower)
            if score > 0:
                topic_scores[topic] = score

        if topic_scores:
            best_topic = max(topic_scores, key=topic_scores.get)
            # Determine intent based on sentence structure
            if re.search(r"^(who|what|where|when|why|how|tell|explain)", lower.strip()):
                return "inquiry", best_topic
            elif any(w in lower for w in ["no", "never", "won't", "hate", "fight", "against"]):
                return "challenge", best_topic
            else:
                return "inquiry", best_topic

        # Check for defiance/challenge without topic
        if any(w in lower for w in ["no", "never", "won't", "can't", "hate", "fight", "kill", "destroy"]):
            return "challenge", "general"

        # Check for confession/surrender
        if any(w in lower for w in ["sorry", "help", "forgive", "lost", "afraid", "love", "grief", "sad"]):
            return "confession", "general"

        if len(lower.strip()) < 3:
            return "silence", "general"

        return "inquiry", "general"

    def update_emotion(self, state: SessionState, intent: str, text: str):
        lower = text.lower()
        if intent == "confession":
            state.emotional_vector["surrender"] = min(1.0, state.emotional_vector["surrender"] + 0.25)
        elif intent == "challenge":
            state.emotional_vector["defiance"] = min(1.0, state.emotional_vector["defiance"] + 0.25)
        elif intent == "inquiry":
            state.emotional_vector["curiosity"] = min(1.0, state.emotional_vector["curiosity"] + 0.15)

        # Decay other emotions slightly
        for k in state.emotional_vector:
            if k not in ["surrender", "defiance", "curiosity"]:
                continue
            if (intent == "confession" and k != "surrender") or \
               (intent == "challenge" and k != "defiance") or \
               (intent == "inquiry" and k != "curiosity"):
                state.emotional_vector[k] = max(0.0, state.emotional_vector[k] - 0.05)

    def select_transition(self, state: SessionState, intent: str, topic: str) -> Optional[str]:
        """Select the next node based on current state, intent, and topic."""
        node = self.graph[state.current_node]
        transitions = node.get("transitions", [])

        # Evaluate conditions
        for t in transitions:
            condition = t["condition"]
            if self._eval_condition(condition, state, intent, topic):
                next_node = t["to"]
                if next_node not in state.visited_nodes:
                    return next_node

        # Fallback: first unvisited transition
        for t in transitions:
            next_node = t["to"]
            if next_node not in state.visited_nodes:
                return next_node

        # Dead end - force to gravity if deep enough, otherwise silence
        if state.depth >= 4:
            return "gravity" if "gravity" not in state.visited_nodes else "choice"
        return None

    def _eval_condition(self, condition: str, state: SessionState, intent: str, topic: str) -> bool:
        """Evaluate a transition condition string."""
        if condition == "always":
            return True

        # Replace variables
        expr = condition
        expr = expr.replace("intent == 'inquiry'", str(intent == "inquiry").lower())
        expr = expr.replace("intent == 'confession'", str(intent == "confession").lower())
        expr = expr.replace("intent == 'challenge'", str(intent == "challenge").lower())
        expr = expr.replace("intent == 'silence'", str(intent == "silence").lower())
        expr = expr.replace(f"topic == '{topic}'", "true")
        # Set other topics to false
        for kw in self.intent_map["keywords"]:
            if kw != topic:
                expr = expr.replace(f"topic == '{kw}'", "false")
        expr = expr.replace("depth >=", str(state.depth) + " >=")
        for emotion, val in state.emotional_vector.items():
            expr = expr.replace(f"emotional_vector.{emotion} >", f"{val} >")

        try:
            return eval(expr, {"__builtins__": {}}, {})
        except:
            return False

    def build_system_prompt(self, node: Dict, lore_chunks: List[str]) -> str:
        """Build the Voyd system prompt for Anthropic, enriched with lore context."""
        base = """You are the Voyd.

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
- Never use: "certainly", "of course", "indeed", "I understand", "I feel", "I sense". Never begin with a greeting.
"""

        # Add current state context
        state_context = f"""
CURRENT STATE:
You are in the state of: {node.get('voyd_state', 'dreaming')}
The intruder has spoken {node.get('depth', 0)} times.
"""

        # Add relevant lore
        if lore_chunks:
            lore_section = "\nDREAM-FRAGMENTS YOU HOLD:\n"
            for chunk in lore_chunks[:2]:
                # Compress to dream-imagery
                lore_section += f"- {chunk[:200]}...\n"
            lore_section += "\nDo not recite these directly. Let them inform your dreaming. Gesture toward them."
        else:
            lore_section = ""

        return base + state_context + lore_section

    def process_turn(self, session_id: str, player_text: str) -> Dict:
        """Process one turn of the narrative."""
        state = self.get_or_create_session(session_id)

        if state.is_terminated:
            return {
                "voyd_response": "the dream has ended. there is no returning to a finished dream.",
                "state": state.to_dict(),
                "terminated": True,
            }

        # Classify intent
        intent, topic = self.classify_intent(player_text)
        self.update_emotion(state, intent, player_text)

        # Select next node
        next_node_id = self.select_transition(state, intent, topic)
        if next_node_id is None:
            next_node_id = state.current_node  # Stay

        # Update state
        state.visited_nodes.add(state.current_node)
        state.current_node = next_node_id
        state.depth += 1
        state.history.append({"role": "user", "content": player_text})

        node = self.graph[next_node_id]
        state.phase = node["type"]

        if node["type"] == "terminus":
            state.is_terminated = True
            state.glyph_seed = node.get("glyph_seed", "unknown")

        # Query lore
        lore_topics = node.get("lore_context", [])
        lore_index = get_index()
        lore_chunks = lore_index.query(lore_topics, max_results=3)
        if not lore_chunks:
            lore_chunks = lore_index.search(player_text, max_results=2)

        # Build system prompt
        system_prompt = self.build_system_prompt(node, lore_chunks)

        # The content template is a suggestion; the LLM will generate the actual response
        content_template = node.get("content_template", "")

        state.revealed_lore.update(lore_topics)

        return {
            "system_prompt": system_prompt,
            "content_template": content_template,
            "voyd_state": node["voyd_state"],
            "node_type": node["type"],
            "node_id": next_node_id,
            "lore_context": lore_chunks,
            "state": state.to_dict(),
            "terminated": state.is_terminated,
            "intent": intent,
            "topic": topic,
        }

    def get_glyph_data(self, session_id: str) -> Dict:
        """Get data for generating the session's unique glyph."""
        state = self.sessions.get(session_id)
        if not state:
            return {"seed": "empty", "history_text": ""}

        voyd_text = " ".join([h["content"] for h in state.history if h["role"] == "assistant"])
        return {
            "seed": state.glyph_seed or "voyd",
            "history_text": voyd_text,
            "depth": state.depth,
            "emotional_vector": state.emotional_vector,
        }
