"""
Lore Index for the Voyd Terminal
Indexes all wiki and book text files for semantic/contextual search.
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
]

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
        """Load all markdown/text files from the wiki."""
        files = list(self.wiki_root.rglob("*.md")) + list(self.wiki_root.rglob("*.txt"))
        for fp in files:
            try:
                text = fp.read_text(encoding="utf-8", errors="ignore")
                # Chunk by paragraphs
                chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 40]
                for chunk in chunks:
                    doc_id = len(self.documents)
                    self.documents.append({
                        "id": doc_id,
                        "source": str(fp.relative_to(self.wiki_root)),
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


# Singleton
_lore_index = None

def get_index() -> LoreIndex:
    global _lore_index
    if _lore_index is None:
        _lore_index = LoreIndex()
    return _lore_index
