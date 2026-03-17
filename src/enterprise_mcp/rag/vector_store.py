"""Vector store with numpy cosine similarity and optional Chroma backend.

Default backend stores vectors in memory with JSON persistence (no external DB).
If ``chromadb`` is installed, an optional Chroma backend is available.
"""

from __future__ import annotations

import json
import logging
import math
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Document:
    """A document stored in the vector store."""

    id: str
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: float = field(default_factory=time.time)


@dataclass
class SearchResult:
    """A single search result with relevance score."""

    id: str
    text: str
    metadata: dict[str, Any]
    score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "metadata": self.metadata,
            "score": round(self.score, 4),
        }


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a < 1e-10 or norm_b < 1e-10:
        return 0.0
    return dot / (norm_a * norm_b)


try:
    import numpy as np

    def _cosine_similarity_np(a: list[float], b: list[float]) -> float:
        va = np.array(a)
        vb = np.array(b)
        dot = np.dot(va, vb)
        norm = np.linalg.norm(va) * np.linalg.norm(vb)
        if norm < 1e-10:
            return 0.0
        return float(dot / norm)

    _cosine_sim = _cosine_similarity_np
except ImportError:
    _cosine_sim = _cosine_similarity


class VectorStore:
    """In-memory vector store with cosine similarity search and JSON persistence.

    Uses numpy for fast similarity computation when available, falling back
    to pure-Python math otherwise.

    Args:
        persist_path: Optional file path for JSON persistence.
                      Documents are saved/loaded automatically.
    """

    def __init__(self, persist_path: str = "") -> None:
        self._documents: dict[str, Document] = {}
        self._persist_path = persist_path
        if persist_path and os.path.exists(persist_path):
            self._load()

    # -- public API -------------------------------------------------------- #

    async def add_document(
        self,
        doc_id: str,
        text: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add or update a document in the store.

        Args:
            doc_id: Unique document identifier.
            text: Document text content.
            embedding: Pre-computed embedding vector.
            metadata: Arbitrary metadata (source, url, title, etc.).
        """
        self._documents[doc_id] = Document(
            id=doc_id,
            text=text,
            embedding=embedding,
            metadata=metadata or {},
        )

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Search for the most similar documents.

        Args:
            query_embedding: Query embedding vector.
            top_k: Maximum number of results to return.
            filter: Optional metadata filter (exact match on each key).

        Returns:
            List of SearchResult objects sorted by descending similarity.
        """
        scored: list[tuple[float, Document]] = []
        for doc in self._documents.values():
            if filter and not self._matches_filter(doc, filter):
                continue
            score = _cosine_sim(query_embedding, doc.embedding)
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            SearchResult(
                id=doc.id,
                text=doc.text,
                metadata=doc.metadata,
                score=score,
            )
            for score, doc in scored[:top_k]
        ]

    async def delete_document(self, doc_id: str) -> bool:
        """Remove a document by ID. Returns True if found and removed."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            return True
        return False

    async def get_document(self, doc_id: str) -> Document | None:
        """Retrieve a document by ID."""
        return self._documents.get(doc_id)

    @property
    def count(self) -> int:
        """Return the number of stored documents."""
        return len(self._documents)

    async def save(self) -> None:
        """Persist all documents to the configured JSON file."""
        if not self._persist_path:
            return
        self._save()

    async def clear(self) -> None:
        """Remove all documents from the store."""
        self._documents.clear()

    def stats(self) -> dict[str, Any]:
        """Return index statistics."""
        sources: dict[str, int] = {}
        for doc in self._documents.values():
            src = doc.metadata.get("source", "unknown")
            sources[src] = sources.get(src, 0) + 1
        return {
            "total_documents": self.count,
            "sources": sources,
        }

    # -- persistence ------------------------------------------------------- #

    def _save(self) -> None:
        Path(self._persist_path).parent.mkdir(parents=True, exist_ok=True)
        data = []
        for doc in self._documents.values():
            data.append(
                {
                    "id": doc.id,
                    "text": doc.text,
                    "embedding": doc.embedding,
                    "metadata": doc.metadata,
                    "updated_at": doc.updated_at,
                }
            )
        with open(self._persist_path, "w") as f:
            json.dump(data, f)
        logger.debug("vector_store_saved", path=self._persist_path, count=len(data))

    def _load(self) -> None:
        try:
            with open(self._persist_path) as f:
                data = json.load(f)
            for item in data:
                self._documents[item["id"]] = Document(
                    id=item["id"],
                    text=item["text"],
                    embedding=item["embedding"],
                    metadata=item.get("metadata", {}),
                    updated_at=item.get("updated_at", 0.0),
                )
            logger.info(
                "vector_store_loaded",
                path=self._persist_path,
                count=len(self._documents),
            )
        except (json.JSONDecodeError, KeyError) as exc:
            logger.warning("vector_store_load_failed", path=self._persist_path, error=str(exc))

    # -- filtering --------------------------------------------------------- #

    @staticmethod
    def _matches_filter(doc: Document, filter: dict[str, Any]) -> bool:
        for key, value in filter.items():
            if doc.metadata.get(key) != value:
                return False
        return True


class ChromaVectorStore:
    """Optional Chroma-backed vector store.

    Requires ``chromadb`` to be installed. Provides the same interface as
    :class:`VectorStore` but delegates storage and search to ChromaDB.
    """

    def __init__(self, collection_name: str = "enterprise_mcp", persist_dir: str = "") -> None:
        import chromadb

        if persist_dir:
            self._client = chromadb.PersistentClient(path=persist_dir)
        else:
            self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    async def add_document(
        self,
        doc_id: str,
        text: str,
        embedding: list[float],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._collection.upsert(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata or {}],
        )

    async def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        kwargs: dict[str, Any] = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
        }
        if filter:
            kwargs["where"] = filter
        results = self._collection.query(**kwargs)

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                score = 1.0 - (results["distances"][0][i] if results["distances"] else 0.0)
                search_results.append(
                    SearchResult(
                        id=doc_id,
                        text=results["documents"][0][i] if results["documents"] else "",
                        metadata=results["metadatas"][0][i] if results["metadatas"] else {},
                        score=score,
                    )
                )
        return search_results

    async def delete_document(self, doc_id: str) -> bool:
        try:
            self._collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    @property
    def count(self) -> int:
        return self._collection.count()

    async def save(self) -> None:
        pass  # Chroma persists automatically

    async def clear(self) -> None:
        self._client.delete_collection(self._collection.name)
        self._collection = self._client.get_or_create_collection(
            name=self._collection.name,
            metadata={"hnsw:space": "cosine"},
        )

    def stats(self) -> dict[str, Any]:
        return {
            "total_documents": self.count,
            "backend": "chromadb",
        }
