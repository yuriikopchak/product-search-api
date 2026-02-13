# app/search/engine.py
import asyncio
import logging
from collections import OrderedDict
import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings
from app.search.filters import apply_filters
from app.search.scorer import score_products

logger = logging.getLogger(__name__)


class SearchEngine:
    def __init__(self, index: dict):
        self.index = index
        self._embedding_cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self._embedding_cache_size = settings.embedding_cache_size
        self._encode_lock = asyncio.Lock()
        self.model = None

    def load_model(self):
        logger.info("Loading JINA CLIP v2 model...")
        self.model = SentenceTransformer("jinaai/jina-clip-v2", trust_remote_code=True)
        self.model.encode(["warmup"], normalize_embeddings=True)
        logger.info("Model loaded!")

    async def get_query_embedding(self, query: str) -> np.ndarray:
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
        filters: dict | None = None,
    ) -> list[str]:
        query_emb = await self.get_query_embedding(query)

        cat_data = self.index[category_id]
        results = score_products(cat_data, query, query_emb)

        if filters:
            results = apply_filters(results, cat_data, filters)

        results.sort(key=lambda x: x[1], reverse=True)

        return [r[0] for r in results]
