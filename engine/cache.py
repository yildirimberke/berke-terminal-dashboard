import time
import threading

_cache = {}
_lock = threading.Lock()

def get_cached(key, ttl_seconds=60):
    """Retrieve data from the thread-safe TTL cache."""
    with _lock:
        entry = _cache.get(key)
        if entry and (time.time() - entry["ts"]) < ttl_seconds:
            return entry["data"]
    return None

def set_cached(key, data):
    """Store data in the thread-safe TTL cache with a current timestamp."""
    with _lock:
        _cache[key] = {"data": data, "ts": time.time()}
