"""
Embedding cache to avoid redundant API calls.

Implements in-memory LRU cache with optional Redis backend.
"""

import hashlib
import time
from collections import OrderedDict
from typing import Any

from src.shared.logging import LoggerMixin


class EmbeddingCache(LoggerMixin):
    """
    LRU cache for text embeddings.

    Features:
    - In-memory caching with size limits
    - TTL (time-to-live) support
    - Cache statistics
    - Content-based keying (hash)
    """

    def __init__(
        self,
        max_size: int = 10000,
        ttl_seconds: int = 86400  # 24 hours
    ):
        """
        Initialize embedding cache.

        Args:
            max_size: Maximum number of cached embeddings
            ttl_seconds: Time-to-live for cached items
        """
        super().__init__()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict[str, tuple[list[float], float]] = OrderedDict()

        # Statistics
        self.hits = 0
        self.misses = 0

        self.logger.info(
            "embedding_cache_initialized",
            max_size=max_size,
            ttl_seconds=ttl_seconds
        )

    def _get_key(self, text: str, model: str) -> str:
        """
        Generate cache key from text and model.

        Args:
            text: Input text
            model: Model identifier

        Returns:
            Cache key (hash)
        """
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()[:32]

    def get(self, text: str, model: str) -> list[float] | None:
        """
        Retrieve embedding from cache.

        Args:
            text: Input text
            model: Model identifier

        Returns:
            Cached embedding or None if not found/expired
        """
        key = self._get_key(text, model)

        if key in self._cache:
            embedding, timestamp = self._cache[key]

            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                self.misses += 1
                return None

            # Move to end (LRU)
            self._cache.move_to_end(key)
            self.hits += 1

            self.logger.debug("cache_hit", key=key[:8])
            return embedding

        self.misses += 1
        return None

    def put(self, text: str, model: str, embedding: list[float]) -> None:
        """
        Store embedding in cache.

        Args:
            text: Input text
            model: Model identifier
            embedding: Embedding vector
        """
        key = self._get_key(text, model)

        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self.logger.debug("cache_eviction", evicted_key=oldest_key[:8])

        self._cache[key] = (embedding, time.time())
        self.logger.debug("cache_put", key=key[:8])

    def clear(self) -> None:
        """Clear all cached embeddings."""
        count = len(self._cache)
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        self.logger.info("cache_cleared", items_removed=count)

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Statistics dictionary
        """
        total_requests = self.hits + self.misses
        hit_rate = self.hits / total_requests if total_requests > 0 else 0.0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

    def info(self) -> str:
        """
        Get cache info string.

        Returns:
            Formatted info string
        """
        stats = self.get_stats()
        return (
            f"EmbeddingCache(size={stats['size']}/{stats['max_size']}, "
            f"hit_rate={stats['hit_rate']:.2%}, "
            f"hits={stats['hits']}, misses={stats['misses']})"
        )
