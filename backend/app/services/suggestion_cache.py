"""
SuggestionCache — Simple in-memory TTL cache for ProjectSuggestions.

Prevents repeated LLM calls for the same category within a short window.
Default TTL: 5 minutes. Keyed on (category, user_tier).
"""
import time
from typing import Any, Dict, Optional, Tuple

_DEFAULT_TTL_SECONDS = 300  # 5 minutes


class SuggestionCache:
    """Thread-safe (for asyncio) in-memory TTL cache for project suggestions."""

    # _store: key -> (payload, expires_at)
    _store: Dict[str, Tuple[Any, float]] = {}
    _hits: int = 0
    _misses: int = 0

    @classmethod
    def _make_key(cls, category: str, user_tier: str = "default") -> str:
        return f"{category.lower().strip()}:{user_tier}"

    @classmethod
    def get(cls, category: str, user_tier: str = "default") -> Optional[Any]:
        """Returns cached suggestions if still valid, else None."""
        key = cls._make_key(category, user_tier)
        entry = cls._store.get(key)
        if entry is not None:
            payload, expires_at = entry
            if time.monotonic() < expires_at:
                cls._hits += 1
                return payload
            # Expired — evict
            del cls._store[key]
        cls._misses += 1
        return None

    @classmethod
    def set(cls, category: str, payload: Any, user_tier: str = "default", ttl: int = _DEFAULT_TTL_SECONDS) -> None:
        """Stores suggestions in cache with the given TTL."""
        key = cls._make_key(category, user_tier)
        cls._store[key] = (payload, time.monotonic() + ttl)

    @classmethod
    def invalidate(cls, category: str, user_tier: str = "default") -> None:
        """Explicitly removes a cache entry."""
        key = cls._make_key(category, user_tier)
        cls._store.pop(key, None)

    @classmethod
    def clear_all(cls) -> None:
        """Clears all entries (used for testing)."""
        cls._store.clear()
        cls._hits = 0
        cls._misses = 0

    @classmethod
    def stats(cls) -> Dict[str, Any]:
        """Returns cache stats."""
        total = cls._hits + cls._misses
        return {
            "hits": cls._hits,
            "misses": cls._misses,
            "total": total,
            "hit_rate_percent": round((cls._hits / max(1, total)) * 100, 1),
            "cached_entries": len(cls._store),
        }
