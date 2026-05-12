"""Small in-process TTL cache for safe read-heavy API responses.

This cache is intentionally process-local. It is suitable for public/semi-static
payloads such as food lists, but not for auth, payment, or user-specific data.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from threading import RLock
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


_store: dict[str, CacheEntry] = {}
_lock = RLock()


def get_cache(key: str) -> Any | None:
    """Return a cached value if present and not expired."""
    now = time.time()
    with _lock:
        entry = _store.get(key)
        if entry is None:
            return None
        if entry.expires_at <= now:
            _store.pop(key, None)
            return None
        return entry.value


def set_cache(key: str, value: Any, ttl_seconds: int) -> None:
    """Store a value with a per-key TTL."""
    with _lock:
        _store[key] = CacheEntry(
            value=value,
            expires_at=time.time() + ttl_seconds,
        )


def delete_cache(key: str) -> None:
    """Delete one cache key if present."""
    with _lock:
        _store.pop(key, None)


def delete_cache_prefix(prefix: str) -> None:
    """Delete every key starting with the supplied prefix."""
    with _lock:
        for key in list(_store):
            if key.startswith(prefix):
                _store.pop(key, None)


def clear_cache() -> None:
    """Clear all in-process cache entries."""
    with _lock:
        _store.clear()
