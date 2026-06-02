"""
Voyd Terminal API
FastAPI backend for the acyclic narrative engine.
"""

import os
import uuid
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .narrative_engine import NarrativeEngine

# Secure API key handling
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    # Try to load from .env if present
    env_path = os.path.expanduser("~/.hermes/.env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.startswith("ANTHROPIC_API_KEY="):
                    ANTHROPIC_API_KEY = line.strip().split("=", 1)[1].strip().strip('"')
                    break

engine = NarrativeEngine()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Voyd Engine initializing...")
    yield
    # Shutdown
    print("Voyd Engine shutting down...")


app = FastAPI(title="Voyd Terminal API", lifespan=lifespan)

# CORS for GitHub Pages frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    session_id: str = ""
    message: str
    model: str = "claude-sonnet-4-20250514"
    portal_value: int = 8
    archetype: str = ""
    player_answer: str = ""


class ChatResponse(BaseModel):
    session_id: str
    voyd_response: str
    node_id: str
    node_type: str
    terminated: bool
    glyph_seed: str = ""


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    if not req.session_id:
        req.session_id = str(uuid.uuid4())

    # Process through narrative engine
    session = engine.get_or_create_session(req.session_id)
    if req.archetype:
        session.archetype = req.archetype
        session.player_answer = req.player_answer
        session.portal_value = req.portal_value

    result = engine.process_turn(req.session_id, req.message)
    state = result["state"]

    if result["terminated"]:
        return ChatResponse(
            session_id=req.session_id,
            voyd_response=result.get("content_template", ""),
            node_id=result["node_id"],
            node_type=result["node_type"],
            terminated=True,
            glyph_seed=state.get("glyph_seed", ""),
        )

    # Call Anthropic API securely server-side
    voyd_text = ""
    if ANTHROPIC_API_KEY:
        try:
            import httpx
            messages = [
                {"role": h["role"], "content": h["content"]}
                for h in state["history"]
            ]
            # Add the user's latest message
            if not messages or messages[-1]["role"] != "user":
                messages.append({"role": "user", "content": req.message})

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "Content-Type": "application/json",
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                    },
                    json={
                        "model": req.model,
                        "max_tokens": 300,
                        "system": result["system_prompt"],
                        "messages": messages[-6:],  # Keep last 6 for context
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    voyd_text = data["content"][0]["text"]
                else:
                    voyd_text = result["content_template"]
        except Exception as e:
            print(f"Anthropic error: {e}")
            voyd_text = result["content_template"]
    else:
        # Fallback to template if no API key
        voyd_text = result["content_template"]

    # Update session history with assistant response
    session = engine.get_or_create_session(req.session_id)
    session.history.append({"role": "assistant", "content": voyd_text})

    return ChatResponse(
        session_id=req.session_id,
        voyd_response=voyd_text,
        node_id=result["node_id"],
        node_type=result["node_type"],
        terminated=result["terminated"],
        glyph_seed=state.get("glyph_seed", ""),
    )


@app.get("/api/session/{session_id}")
async def get_session(session_id: str):
    session = engine.get_or_create_session(session_id)
    return session.to_dict()


@app.get("/api/glyph/{session_id}")
async def get_glyph(session_id: str):
    return engine.get_glyph_data(session_id)


@app.get("/api/health")
async def health():
    return {"status": "listening", "api_key_configured": bool(ANTHROPIC_API_KEY)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8765)
