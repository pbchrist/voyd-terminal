"""
Graph RAG integration for the Voyd Terminal.
Loads the knowledge graph, passages, and ChromaDB index
for semantic retrieval of canon passages.
"""

import json
import pickle
from pathlib import Path
from typing import List

GRAPH_RAG_DIR = Path("/home/patrick/voyd_graph_rag")
PASSAGES_PATH = GRAPH_RAG_DIR / "passages.json"
GRAPH_PATH = GRAPH_RAG_DIR / "knowledge_graph.pkl"
CHROMA_PATH = str(GRAPH_RAG_DIR / "chromadb")

_chroma_client = None
_collection = None
_model = None
_passages = None
_graph = None


def _load():
    global _chroma_client, _collection, _model, _passages, _graph
    if _collection is not None:
        return

    import chromadb
    from sentence_transformers import SentenceTransformer

    _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    _collection = _chroma_client.get_collection("voyd_passages")

    with open(PASSAGES_PATH, encoding="utf-8") as f:
        _passages = json.load(f)

    with open(GRAPH_PATH, "rb") as f:
        _graph = pickle.load(f)

    _model = SentenceTransformer("all-MiniLM-L6-v2")


def query_passages(query_text: str, top_k: int = 3) -> List[str]:
    """Return top-k passage texts relevant to the query."""
    try:
        _load()
    except Exception as e:
        print(f"GraphRAG load error: {e}")
        return []

    try:
        q_emb = _model.encode([query_text]).tolist()
        results = _collection.query(
            query_embeddings=q_emb,
            n_results=top_k,
            include=["documents"],
        )
        return results["documents"][0]
    except Exception as e:
        print(f"GraphRAG query error: {e}")
        return []
