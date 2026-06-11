"""
Lore Index for the Voyd Terminal
Indexes all wiki and book text files for semantic/contextual search.
Falls back to keyword search if ChromaDB is unavailable.
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Tuple

WIKI_ROOT = Path("/home/patrick/Gate_of_Nyandor")
BOOK_FILES = [
    "/home/patrick/Gate_of_Nyandor/book1_text.txt",
    "/home/patrick/Gate_of_Nyandor/book2_text.txt",
    "/home/patrick/voyd-terminal/data/voyd_canon_mythography.md",
]

CHROMA_DB_PATH = "/home/patrick/voyd_graph_rag/chromadb"

LORE_TOPICS = {
    "voyd_entity": ["voyd", "void", "blackness", "singularity", "dimension", "potential", "darkness before"],
    "voyd_magic": ["voyd magic", "voyd portal", "forbidden voyd", "black disc", "marble-sized"],
    "soryn": ["sory'n", "soryn", "daughter of tol", "archmage's daughter", "sorrowing"],
    "orachys": ["orachys", "father", "six hundred", "694", "singularity", "attempts"],
    "denidrata_sol": ["denidrata", "sol", "first era", "archmage", "diary", "vault"],
    "leoran": ["leoran", "creator", "endless one", "mind of leoran", "source"],
    "great_severing": ["great severing", "severing", "shattered", "collapse", "timeline", "wished away"],
    "null_state": ["null state", "meditative", "trance", "construct", "intention becomes"],
    "mewniverse": ["mewniverse", "universe", "nyandor", "world", "realms"],
    "wellsprings": ["wellspring", "ashai", "imbibarium", "cazza", "nyand breathes"],
    "magic_system": ["voreath", "common spark", "felix magistrae", "pawsition", "conjuration", "element"],
    "timestreams": ["timestream", "timeline", "parallel", "divergent", "reality"],
    "portal": ["portal", "gateway", "door", "opens from inside"],
    "light_test": ["light test", "choice point", "free will", "selfless", "intention"],
    "constructs": ["construct", "mental visualization", "realm", "inner realm"],
    "guild": ["guild", "magical guild", "voreath", "templu", "acatdemy", "high council"],
    "strays": ["strays", "forest primeval", "mother ertree", "clowder", "resistance"],
    "cat": ["c.a.t.", "creator of all tales", "narrator", "frame", "dice"],
}


class LoreIndex:
    def __init__(self, wiki_root: Path = WIKI_ROOT):
        self.wiki_root = wiki_root
        self.documents: List[Dict] = []
        self.topic_index: Dict[str, List[int]] = {t: [] for t in LORE_TOPICS}
        self._load_all()

    def _load_all(self):
        """Load all markdown/text files from the wiki, plus the explicit BOOK_FILES."""
        files = list(self.wiki_root.rglob("*.md")) + list(self.wiki_root.rglob("*.txt"))
        files += [Path(p) for p in BOOK_FILES]
        seen_paths = set()
        for fp in files:
            try:
                resolved = fp.resolve()
                if resolved in seen_paths or not resolved.exists():
                    continue
                seen_paths.add(resolved)
                try:
                    source = str(fp.relative_to(self.wiki_root))
                except ValueError:
                    source = fp.name
                text = fp.read_text(encoding="utf-8", errors="ignore")
                # Chunk by paragraphs
                chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 40]
                for chunk in chunks:
                    doc_id = len(self.documents)
                    self.documents.append({
                        "id": doc_id,
                        "source": source,
                        "text": chunk,
                    })
                    # Index by topic
                    lower = chunk.lower()
                    for topic, keywords in LORE_TOPICS.items():
                        if any(kw in lower for kw in keywords):
                            self.topic_index[topic].append(doc_id)
            except Exception:
                continue

    def query(self, topics: List[str], max_results: int = 3) -> List[str]:
        """Retrieve relevant lore chunks for given topics."""
        seen = set()
        results = []
        for topic in topics:
            for doc_id in self.topic_index.get(topic, []):
                if doc_id not in seen and len(results) < max_results:
                    seen.add(doc_id)
                    results.append(self.documents[doc_id]["text"])
        return results

    def search(self, query_text: str, max_results: int = 3) -> List[str]:
        """Free-text search across all documents."""
        words = re.findall(r"\b\w+\b", query_text.lower())
        scored = []
        for doc in self.documents:
            lower = doc["text"].lower()
            score = sum(3 if w in lower else 0 for w in words)
            if score > 0:
                scored.append((score, doc["text"]))
        scored.sort(reverse=True)
        return [t for _, t in scored[:max_results]]

    def query_chromadb(self, query_text: str, n_results: int = 3) -> List[str]:
        """Query the ChromaDB RAG store for semantically relevant passages."""
        try:
            import chromadb
            client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
            collections = client.list_collections()
            if not collections:
                return []
            col_name = collections[0].name if hasattr(collections[0], "name") else str(collections[0])
            collection = client.get_collection(col_name)
            results = collection.query(
                query_texts=[query_text],
                n_results=n_results,
            )
            docs = results.get("documents", [[]])[0]
            return [d for d in docs if d]
        except Exception:
            return []

    def query_rag(self, query_text: str, topics: List[str] = None, max_results: int = 3) -> List[str]:
        """Try ChromaDB first, fall back to keyword index."""
        chroma_results = self.query_chromadb(query_text, n_results=max_results)
        if chroma_results:
            return chroma_results
        if topics:
            topic_results = self.query(topics, max_results=max_results)
            if topic_results:
                return topic_results
        return self.search(query_text, max_results=max_results)


# Singleton
_lore_index = None

def get_index() -> LoreIndex:
    global _lore_index
    if _lore_index is None:
        _lore_index = LoreIndex()
    return _lore_index
