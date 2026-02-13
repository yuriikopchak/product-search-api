"""Search engine runtime for embedding-based product retrieval."""

import asyncio
import logging
from collections import OrderedDict
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.search.filters import apply_filters
from app.search.scorer import score_products

logger = logging.getLogger(__name__)


class SearchEngine:
    """Serve semantic search over preloaded category indices."""

    def __init__(self, index: dict[str, dict[str, Any]]) -> None:
        """Initialize the search engine with in-memory index data.

        Args:
            index: Per-category index with product IDs, embeddings, names, and filter metadata.
        """
        self.index = index
        self._embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._embedding_cache_size = settings.embedding_cache_size
        self._encode_lock = asyncio.Lock()
        self.model: SentenceTransformer | None = None

    def load_model(self) -> None:
        """Load and warm up the embedding model used for query encoding."""
        logger.info("Loading JINA CLIP v2 model...")
        self.model = SentenceTransformer("jinaai/jina-clip-v2", trust_remote_code=True)
        self.model.encode(["warmup"], normalize_embeddings=True)
        logger.info("Model loaded!")

    async def get_query_embedding(self, query: str) -> np.ndarray:
        """Return a normalized embedding for a search query.

        Uses an LRU cache to avoid recomputing embeddings for repeated queries.
        Embedding generation is serialized via lock to reduce memory spikes.

        Args:
            query: Free-text user query.

        Returns:
            Query embedding vector as float32 NumPy array.
        """
        if self.model is None:
            raise RuntimeError(
                "Search model is not loaded. Call load_model() before search."
            )

        cache_key = query.strip().lower()
        if self._embedding_cache_size > 0 and cache_key in self._embedding_cache:
            self._embedding_cache.move_to_end(cache_key)
            return self._embedding_cache[cache_key]

        async with self._encode_lock:
            if self._embedding_cache_size > 0 and cache_key in self._embedding_cache:
                self._embedding_cache.move_to_end(cache_key)
                return self._embedding_cache[cache_key]

            embedding = await asyncio.to_thread(
                lambda: self.model.encode([query], normalize_embeddings=True)[0]
            )
            embedding = np.array(embedding, dtype=np.float32)

            if self._embedding_cache_size > 0:
                self._embedding_cache[cache_key] = embedding
                self._embedding_cache.move_to_end(cache_key)
                if len(self._embedding_cache) > self._embedding_cache_size:
                    self._embedding_cache.popitem(last=False)
            return embedding

    async def search(
        self,
        category_id: str,
        query: str,
        filters: dict[str, Any] | None = None,
    ) -> list[str]:
        """Search products in a category and return ranked product IDs.

        Args:
            category_id: Target category identifier from settings/endpoints map.
            query: Free-text query to score against product embeddings.
            filters: Optional endpoint-specific filters (dimensions, booleans, etc.).

        Returns:
            Product IDs sorted by descending relevance score.
        """
        query_emb = await self.get_query_embedding(query)

        cat_data = self.index[category_id]
        results = score_products(cat_data, query, query_emb)

        if filters:
            results = apply_filters(results, cat_data, filters)

        results.sort(key=lambda x: x[1], reverse=True)

        # Remove products that are not good matches
        if results:
            top_score = results[0][1]
            threshold = max(0.10, top_score * 0.25)
            results = [(pid, s) for pid, s in results if s >= threshold]

        return [r[0] for r in results]
