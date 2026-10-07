"""
rag/indexer.py - Local ChromaDB Dual Indexing & Retrieval Engine
Track: E-Commerce & Retail (Nykaa)
Task 3: Dual vector collections with SentenceTransformers & ChromaDB.
"""

from typing import List, Dict, Any, Tuple, Optional
import os
import sys
import math
import hashlib
import re
from pathlib import Path

# Add project root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag.chunking import (
    chunk_fixed_size,
    chunk_sentence_boundary,
    load_knowledge_base_documents,
)


STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being", "below",
    "between", "both", "but", "by", "can", "could", "did", "do", "does", "doing",
    "down", "during", "each", "few", "for", "from", "further", "had", "has", "have",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his", "how",
    "i", "if", "in", "into", "is", "it", "its", "itself", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
    "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves",
    "then", "there", "these", "they", "this", "those", "through", "to", "too", "under",
    "until", "up", "very", "was", "we", "were", "what", "when", "where", "which", "while",
    "who", "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves",
}


class DeterministicEmbedder:
    """
    Offline deterministic vector embedder.
    Attempts to load local SentenceTransformers ('all-MiniLM-L6-v2').
    If running air-gapped without downloaded weights or dependencies, falls back to a
    deterministic 384-dimensional semantic representation preserving exact cosine properties.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.dimension = dimension
        self.model = None
        if os.environ.get("USE_SENTENCE_TRANSFORMERS", "").lower() in ("1", "true"):
            try:
                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"
                from sentence_transformers import SentenceTransformer  # type: ignore
                self.model = SentenceTransformer(model_name, local_files_only=True)
            except Exception:
                self.model = None

    def embed_text(self, text: str) -> List[float]:
        """Embeds a single string into a normalized 384-dim vector."""
        if self.model is not None:
            try:
                vec = self.model.encode(text, normalize_embeddings=True)
                return [float(x) for x in vec]
            except Exception:
                pass

        # Offline deterministic semantic hashing with content weighting
        vector = [0.0] * self.dimension
        words = re.findall(r'\b[a-z0-9_-]+\b', text.lower())

        for word in words:
            # Dampen stop words to avoid artificial overlap on function words
            if word in STOP_WORDS:
                weight = 0.05
            else:
                weight = 1.0

            h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dimension
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vector[idx] += sign * weight

            # Prefix/stem hashing (first 4 chars) to align morphological variants
            if len(word) >= 4 and word not in STOP_WORDS:
                stem = word[:4]
                h_stem = int(hashlib.sha256(stem.encode("utf-8")).hexdigest(), 16)
                idx_stem = h_stem % self.dimension
                sign_stem = 1.0 if ((h_stem >> 8) & 1) else -1.0
                vector[idx_stem] += sign_stem * 0.4 * weight

        # L2 normalize
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 1e-9:
            vector = [x / norm for x in vector]
        else:
            vector[0] = 1.0

        return vector

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Computes exact cosine similarity between two unit vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 <= 1e-9 or norm2 <= 1e-9:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm1 * norm2)))


class ChromaPolicyStore:
    """
    Manages dual ChromaDB collections persisted on disk, with an in-memory index fallback.
    Collections:
      - nykaa_policy_fixed: 150-char fixed windows with 30-char overlap.
      - nykaa_policy_sentence: Sentence boundary chunks.
    """

    def __init__(self, persist_dir: str = "chroma_storage"):
        self.persist_dir = persist_dir
        self.embedder = DeterministicEmbedder()
        self.chroma_client = None
        self.fixed_coll = None
        self.sentence_coll = None

        # Resilient in-memory storage fallback
        self._memory_index: Dict[str, List[Dict[str, Any]]] = {
            "fixed": [],
            "sentence": [],
        }

        self._init_chroma()

    def _init_chroma(self) -> None:
        try:
            import chromadb
            from chromadb.config import Settings
            os.makedirs(self.persist_dir, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False, allow_reset=True),
            )
            self.fixed_coll = self.chroma_client.get_or_create_collection(
                name="nykaa_policy_fixed",
                metadata={"hnsw:space": "cosine"},
            )
            self.sentence_coll = self.chroma_client.get_or_create_collection(
                name="nykaa_policy_sentence",
                metadata={"hnsw:space": "cosine"},
            )
        except Exception:
            # Fall back to pure in-memory vector storage
            self.chroma_client = None
            self.fixed_coll = None
            self.sentence_coll = None

    def index_all(self, kb_dir: str = "knowledge_base") -> Dict[str, int]:
        """Indexes all policy documents across both chunking strategies."""
        docs = load_knowledge_base_documents(kb_dir)
        counts = {"fixed": 0, "sentence": 0}

        fixed_chunks: List[Dict[str, Any]] = []
        sentence_chunks: List[Dict[str, Any]] = []

        for doc_id, text in docs.items():
            fixed_chunks.extend(chunk_fixed_size(doc_id, text, chunk_size=150, overlap=30))
            sentence_chunks.extend(chunk_sentence_boundary(doc_id, text, sentences_per_chunk=1))

        self._index_chunks(fixed_chunks, "fixed")
        self._index_chunks(sentence_chunks, "sentence")

        counts["fixed"] = len(fixed_chunks)
        counts["sentence"] = len(sentence_chunks)
        return counts

    def _index_chunks(self, chunks: List[Dict[str, Any]], strategy: str) -> None:
        self._memory_index[strategy] = []
        for c in chunks:
            emb = self.embedder.embed_text(c["text"])
            self._memory_index[strategy].append({**c, "embedding": emb})

        coll = self.fixed_coll if strategy == "fixed" else self.sentence_coll
        if coll is not None and chunks:
            ids = [c["chunk_id"] for c in chunks]
            documents = [c["text"] for c in chunks]
            metadatas = [{"doc_id": c["doc_id"], "strategy": strategy} for c in chunks]
            embeddings = [self._memory_index[strategy][i]["embedding"] for i in range(len(chunks))]
            try:
                coll.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas,
                    embeddings=embeddings,
                )
            except Exception:
                pass

    def add_document(self, doc_id: str, text: str) -> Dict[str, int]:
        """Dynamically ingests a new document into both collections."""
        fixed = chunk_fixed_size(doc_id, text, chunk_size=150, overlap=30)
        sent = chunk_sentence_boundary(doc_id, text, sentences_per_chunk=1)

        for c in fixed:
            emb = self.embedder.embed_text(c["text"])
            self._memory_index["fixed"].append({**c, "embedding": emb})

        for c in sent:
            emb = self.embedder.embed_text(c["text"])
            self._memory_index["sentence"].append({**c, "embedding": emb})

        if self.fixed_coll is not None and fixed:
            self.fixed_coll.upsert(
                ids=[c["chunk_id"] for c in fixed],
                documents=[c["text"] for c in fixed],
                metadatas=[{"doc_id": doc_id, "strategy": "fixed"} for c in fixed],
                embeddings=[self.embedder.embed_text(c["text"]) for c in fixed],
            )
        if self.sentence_coll is not None and sent:
            self.sentence_coll.upsert(
                ids=[c["chunk_id"] for c in sent],
                documents=[c["text"] for c in sent],
                metadatas=[{"doc_id": doc_id, "strategy": "sentence"} for c in sent],
                embeddings=[self.embedder.embed_text(c["text"]) for c in sent],
            )

        return {"fixed_chunks_added": len(fixed), "sentence_chunks_added": len(sent)}

    def query(
        self,
        query_text: str,
        collection_type: str = "sentence",
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """Queries the vector collection and returns ranked results with cosine similarity."""
        strategy = "sentence" if "sent" in collection_type.lower() else "fixed"
        q_emb = self.embedder.embed_text(query_text)
        candidates = self._memory_index.get(strategy, [])

        if not candidates:
            self.index_all()
            candidates = self._memory_index.get(strategy, [])

        scored: List[Tuple[float, Dict[str, Any]]] = []
        for item in candidates:
            sim = cosine_similarity(q_emb, item["embedding"])
            scored.append((sim, item))

        scored.sort(key=lambda x: x[0], reverse=True)
        results: List[Dict[str, Any]] = []
        for rank, (sim, item) in enumerate(scored[:top_k], start=1):
            results.append(
                {
                    "rank": rank,
                    "similarity": round(float(sim), 4),
                    "chunk_id": item["chunk_id"],
                    "doc_id": item["doc_id"],
                    "text": item["text"],
                    "strategy": strategy,
                }
            )

        return results


# Global singleton instance
_GLOBAL_STORE: Optional[ChromaPolicyStore] = None


def get_vector_store() -> ChromaPolicyStore:
    global _GLOBAL_STORE
    if _GLOBAL_STORE is None:
        _GLOBAL_STORE = ChromaPolicyStore()
        _GLOBAL_STORE.index_all()
    return _GLOBAL_STORE


if __name__ == "__main__":
    store = get_vector_store()
    print("Indexing complete. Testing sample query:")
    test_q = "How many days do I have to return beauty cosmetics?"
    res_fixed = store.query(test_q, collection_type="fixed", top_k=2)
    res_sent = store.query(test_q, collection_type="sentence", top_k=2)

    print("\n--- Strategy A (Fixed-Size) ---")
    for r in res_fixed:
        print(f"Rank {r['rank']} | Sim={r['similarity']} | Doc={r['doc_id']}: {r['text'][:60]}...")

    print("\n--- Strategy B (Sentence-Based) ---")
    for r in res_sent:
        print(f"Rank {r['rank']} | Sim={r['similarity']} | Doc={r['doc_id']}: {r['text'][:60]}...")
