"""Embedding service with sentence-transformers and TF-IDF fallback.

Uses all-MiniLM-L6-v2 (local, no API key) when sentence-transformers is installed.
Falls back to scikit-learn TF-IDF when it is not available.
"""

import hashlib
import logging
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)

# Lazy-loaded backends
_model: Any = None
_tfidf_vectorizer: Any = None
_backend: str = ""


def _detect_backend() -> str:
    """Detect available embedding backend."""
    global _backend
    if _backend:
        return _backend
    try:
        import sentence_transformers  # noqa: F401

        _backend = "sentence-transformers"
    except ImportError:
        try:
            import sklearn  # noqa: F401

            _backend = "tfidf"
        except ImportError:
            _backend = "simple"
    logger.info("embedding_backend_selected", backend=_backend)
    return _backend


class EmbeddingService:
    """Generate text embeddings using local models (no API key required).

    Supports three backends (auto-detected in order of preference):
    1. sentence-transformers (all-MiniLM-L6-v2) — best quality
    2. scikit-learn TF-IDF — decent quality, lighter dependency
    3. Simple hash-based — minimal fallback, no ML dependency

    Embeddings are cached in an LRU cache (up to ``max_cache_size`` entries).
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        max_cache_size: int = 1000,
    ) -> None:
        self._model_name = model_name
        self._max_cache_size = max_cache_size
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._dimension: int | None = None

    # -- public API -------------------------------------------------------- #

    @property
    def backend(self) -> str:
        """Return the active embedding backend name."""
        return _detect_backend()

    @property
    def dimension(self) -> int:
        """Return the embedding vector dimension."""
        if self._dimension is not None:
            return self._dimension
        backend = _detect_backend()
        if backend == "sentence-transformers":
            self._dimension = 384  # MiniLM-L6-v2 output dim
        elif backend == "tfidf":
            self._dimension = 256
        else:
            self._dimension = 128
        return self._dimension

    async def embed_text(self, text: str) -> list[float]:
        """Generate an embedding vector for a single text.

        Args:
            text: Input text to embed.

        Returns:
            Embedding vector as a list of floats.
        """
        cache_key = self._cache_key(text)
        if cache_key in self._cache:
            self._cache.move_to_end(cache_key)
            return self._cache[cache_key]

        backend = _detect_backend()
        if backend == "sentence-transformers":
            vec = self._embed_st(text)
        elif backend == "tfidf":
            vec = self._embed_tfidf(text)
        else:
            vec = self._embed_simple(text)

        self._put_cache(cache_key, vec)
        return vec

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embedding vectors for multiple texts.

        Cached entries are reused; only uncached texts hit the model.

        Args:
            texts: List of input texts to embed.

        Returns:
            List of embedding vectors (same order as input).
        """
        results: list[list[float] | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            if cache_key in self._cache:
                self._cache.move_to_end(cache_key)
                results[i] = self._cache[cache_key]
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        if uncached_texts:
            backend = _detect_backend()
            if backend == "sentence-transformers":
                vectors = self._embed_st_batch(uncached_texts)
            else:
                vectors = [
                    (
                        self._embed_tfidf(t)
                        if backend == "tfidf"
                        else self._embed_simple(t)
                    )
                    for t in uncached_texts
                ]

            for idx, vec in zip(uncached_indices, vectors):
                results[idx] = vec
                self._put_cache(self._cache_key(texts[idx]), vec)

        return results  # type: ignore[return-value]

    # -- sentence-transformers backend ------------------------------------- #

    def _get_st_model(self) -> Any:
        global _model
        if _model is None:
            from sentence_transformers import SentenceTransformer

            _model = SentenceTransformer(self._model_name)
            logger.info("sentence_transformer_loaded", model=self._model_name)
        return _model

    def _embed_st(self, text: str) -> list[float]:
        model = self._get_st_model()
        vec = model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def _embed_st_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._get_st_model()
        vecs = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return [v.tolist() for v in vecs]

    # -- TF-IDF fallback --------------------------------------------------- #

    def _get_tfidf(self) -> Any:
        global _tfidf_vectorizer
        if _tfidf_vectorizer is None:
            from sklearn.feature_extraction.text import TfidfVectorizer

            _tfidf_vectorizer = TfidfVectorizer(max_features=256)
            # Fit on a minimal corpus so transform works on single docs
            _tfidf_vectorizer.fit(["initialization corpus for tfidf vectorizer"])
            logger.info("tfidf_vectorizer_initialized")
        return _tfidf_vectorizer

    def _embed_tfidf(self, text: str) -> list[float]:
        vectorizer = self._get_tfidf()
        vec = vectorizer.transform([text]).toarray()[0]
        # Pad or truncate to fixed dimension
        result = list(vec[: self.dimension])
        while len(result) < self.dimension:
            result.append(0.0)
        return result

    # -- Simple hash fallback ---------------------------------------------- #

    def _embed_simple(self, text: str) -> list[float]:
        """Hash-based pseudo-embedding for environments with no ML libs."""
        dim = self.dimension
        digest = hashlib.sha512(text.lower().encode()).hexdigest()
        vec = []
        for i in range(dim):
            chunk = digest[(i * 2) % len(digest): (i * 2) % len(digest) + 2]
            vec.append((int(chunk, 16) - 128) / 128.0)
        # Normalize
        norm = max(sum(v * v for v in vec) ** 0.5, 1e-10)
        return [v / norm for v in vec]

    # -- cache helpers ----------------------------------------------------- #

    def _cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def _put_cache(self, key: str, value: list[float]) -> None:
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self._max_cache_size:
            self._cache.popitem(last=False)
