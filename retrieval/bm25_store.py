import math
import re
import json
import os
from typing import List, Dict, Any, Tuple, Optional
from retrieval.models import RetrievedChunk

def default_tokenize(text: str) -> List[str]:
    """Tokenizes string into lowercase alphanumeric tokens."""
    if not text:
        return []
    return re.findall(r'\w+', text.lower())

class BM25Index:
    """Standalone, lightweight BM25Okapi lexical search index."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_count = 0
        self.avg_doc_len = 0.0
        self.doc_lengths: List[int] = []
        self.doc_term_freqs: List[Dict[str, int]] = []
        self.doc_freqs: Dict[str, int] = {}
        self.chunks: List[Dict[str, Any]] = []  # dict with 'chunk_id', 'doc_id', 'text', 'metadata'

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> None:
        """Indexes a list of text chunk dictionaries."""
        for idx, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            tokens = default_tokenize(text)
            doc_len = len(tokens)

            # Compute Term Frequencies for this document chunk
            tf = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1

            # Update Document Frequency (DF) across index
            for token in tf.keys():
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

            self.doc_lengths.append(doc_len)
            self.doc_term_freqs.append(tf)

            chunk_meta = chunk.get("metadata", {}).copy()
            chunk_id = chunk_meta.get("chunk_id") or f"doc_{chunk_meta.get('document_id', 0)}_chk_{idx}"
            doc_id = chunk_meta.get("document_id", 0)

            self.chunks.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "text": text,
                "metadata": chunk_meta
            })

        self.doc_count = len(self.chunks)
        if self.doc_count > 0:
            self.avg_doc_len = sum(self.doc_lengths) / float(self.doc_count)

    def search(self, query: str, top_k: int = 5) -> List[RetrievedChunk]:
        """Queries the BM25 index and returns top-k ranked RetrievedChunk objects."""
        if not query or self.doc_count == 0:
            return []

        query_tokens = default_tokenize(query)
        if not query_tokens:
            return []

        scores: List[float] = [0.0] * self.doc_count

        for token in query_tokens:
            if token not in self.doc_freqs:
                continue

            df = self.doc_freqs[token]
            # Standard BM25 IDF
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)

            for i in range(self.doc_count):
                tf = self.doc_term_freqs[i].get(token, 0)
                if tf > 0:
                    doc_len = self.doc_lengths[i]
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / (self.avg_doc_len or 1.0)))
                    scores[i] += idf * (numerator / denominator)

        # Sort indices by score descending
        ranked_indices = sorted(
            [i for i in range(self.doc_count) if scores[i] > 0.0],
            key=lambda i: scores[i],
            reverse=True
        )[:top_k]

        results = []
        for i in ranked_indices:
            c = self.chunks[i]
            results.append(RetrievedChunk(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                text=c["text"],
                metadata=c["metadata"],
                score=scores[i],
                retrieval_method="bm25"
            ))

        return results

    def save_to_json(self, filepath: str) -> None:
        """Serializes BM25 index to a JSON file."""
        data = {
            "k1": self.k1,
            "b": self.b,
            "doc_count": self.doc_count,
            "avg_doc_len": self.avg_doc_len,
            "doc_lengths": self.doc_lengths,
            "doc_term_freqs": self.doc_term_freqs,
            "doc_freqs": self.doc_freqs,
            "chunks": self.chunks
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_json(cls, filepath: str) -> Optional['BM25Index']:
        """Loads BM25 index from a JSON file."""
        if not os.path.exists(filepath):
            return None
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            index = cls(k1=data.get("k1", 1.5), b=data.get("b", 0.75))
            index.doc_count = data.get("doc_count", 0)
            index.avg_doc_len = data.get("avg_doc_len", 0.0)
            index.doc_lengths = data.get("doc_lengths", [])
            index.doc_term_freqs = data.get("doc_term_freqs", [])
            index.doc_freqs = data.get("doc_freqs", {})
            index.chunks = data.get("chunks", [])
            return index
        except Exception:
            return None

    @classmethod
    def merge_indices(cls, indices: List['BM25Index']) -> Optional['BM25Index']:
        """Merges multiple BM25Index instances into a single combined index."""
        valid_indices = [idx for idx in indices if idx and idx.doc_count > 0]
        if not valid_indices:
            return None

        merged = cls(k1=valid_indices[0].k1, b=valid_indices[0].b)
        all_chunks = []
        for idx in valid_indices:
            all_chunks.extend(idx.chunks)

        merged.add_chunks(all_chunks)
        return merged
