"""
Cache System Example - sqbooster

A TTL-based cache with decorator pattern and function memoization.
"""

import time
import tempfile
import os
from datetime import datetime, timedelta
import sqbooster


class CacheManager:
    def __init__(self, db):
        self.db = db

    def set(self, key, value, ttl_seconds=3600):
        entry = {
            "value": value,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat(),
        }
        self.db.write(f"cache:{key}", entry)

    def get(self, key):
        entry = self.db.read(f"cache:{key}")
        if entry is None:
            return None
        if datetime.now() > datetime.fromisoformat(entry["expires_at"]):
            self.db.delete_key(f"cache:{key}")
            return None
        return entry["value"]

    def delete(self, key):
        self.db.delete_key(f"cache:{key}")

    def clear(self):
        for key in self.db.keys("cache:"):
            self.db.delete_key(key)

    def stats(self):
        keys = self.db.keys("cache:")
        total = len(keys)
        valid = 0
        for key in keys:
            entry = self.db.read(key)
            if entry and datetime.now() <= datetime.fromisoformat(entry["expires_at"]):
                valid += 1
        return {"total": total, "valid": valid, "expired": total - valid}


def memoize(cache, ttl=60):
    def decorator(func):
        def wrapper(*args):
            cache_key = f"{func.__name__}:{args}"
            result = cache.get(cache_key)
            if result is not None:
                print(f"  [CACHE HIT] {func.__name__}{args}")
                return result
            print(f"  [CACHE MISS] {func.__name__}{args}")
            result = func(*args)
            cache.set(cache_key, result, ttl_seconds=ttl)
            return result
        return wrapper
    return decorator


def expensive_computation(n):
    time.sleep(0.1)
    return sum(i * i for i in range(n))


def main():
    print("=== Cache System Example ===\n")

    print("--- SQLite Cache ---")
    cache = CacheManager(sqbooster.sqlite())

    cache.set("user:1", {"name": "Alice", "role": "admin"}, ttl_seconds=10)
    cache.set("user:2", {"name": "Bob", "role": "user"}, ttl_seconds=10)

    print(f"  user:1 = {cache.get('user:1')}")
    print(f"  user:2 = {cache.get('user:2')}")
    print(f"  user:3 = {cache.get('user:3')}")
    print(f"  Stats: {cache.stats()}")

    print("\n--- Memoized Function ---")
    cached_compute = memoize(cache, ttl=30)(expensive_computation)

    result1 = cached_compute(100)
    print(f"  Result: {result1}")

    result2 = cached_compute(100)
    print(f"  Result: {result2}")

    result3 = cached_compute(200)
    print(f"  Result: {result3}")

    print(f"  Stats: {cache.stats()}")

    print("\n--- JSON Cache ---")
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()

    json_cache = CacheManager(sqbooster.json(tmp.name))
    json_cache.set("theme", {"dark": True, "font_size": 14})
    print(f"  theme = {json_cache.get('theme')}")

    os.unlink(tmp.name)

    print("\nDone!")


if __name__ == "__main__":
    main()
