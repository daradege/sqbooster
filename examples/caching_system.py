"""
Caching System Example - sqbooster

A caching system using sqbooster with different storage backends and cache strategies.
"""

import time
import hashlib
import json
from typing import Any, Optional, Callable
from datetime import datetime, timedelta
import sqbooster


class CacheManager:
    def __init__(self, db):
        self.db = db

    def _generate_key(self, key: str, namespace: str = "default") -> str:
        return f"{namespace}:{key}"

    def _is_expired(self, cache_entry: dict) -> bool:
        if "expires_at" not in cache_entry:
            return False
        expires_at = datetime.fromisoformat(cache_entry["expires_at"])
        return datetime.now() > expires_at

    def set(self, key: str, value: Any, ttl: int = 3600, namespace: str = "default"):
        cache_key = self._generate_key(key, namespace)
        cache_entry = {
            "value": value,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=ttl)).isoformat(),
            "hit_count": 0
        }
        self.db.write(cache_key, cache_entry)

    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        cache_key = self._generate_key(key, namespace)

        if not self.db.exists(cache_key):
            return None

        cache_entry = self.db.read(cache_key)

        if self._is_expired(cache_entry):
            self.db.delete_key(cache_key)
            return None

        cache_entry["hit_count"] += 1
        cache_entry["last_accessed"] = datetime.now().isoformat()
        self.db.write(cache_key, cache_entry)

        return cache_entry["value"]

    def delete(self, key: str, namespace: str = "default"):
        cache_key = self._generate_key(key, namespace)
        self.db.delete_key(cache_key)

    def get_stats(self, key: str, namespace: str = "default") -> Optional[dict]:
        cache_key = self._generate_key(key, namespace)

        if not self.db.exists(cache_key):
            return None

        cache_entry = self.db.read(cache_key)

        return {
            "created_at": cache_entry.get("created_at"),
            "expires_at": cache_entry.get("expires_at"),
            "hit_count": cache_entry.get("hit_count", 0),
            "last_accessed": cache_entry.get("last_accessed"),
            "is_expired": self._is_expired(cache_entry)
        }


def cache_decorator(cache_manager: CacheManager, ttl: int = 3600, namespace: str = "functions"):
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            key = hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()

            cached_result = cache_manager.get(key, namespace)
            if cached_result is not None:
                print(f"Cache HIT for {func.__name__}")
                return cached_result

            print(f"Cache MISS for {func.__name__}")
            result = func(*args, **kwargs)
            cache_manager.set(key, result, ttl, namespace)
            return result

        return wrapper
    return decorator


def expensive_computation(n: int) -> int:
    print(f"Performing expensive computation for n={n}")
    time.sleep(2)
    return sum(i * i for i in range(n))


def fetch_user_data(user_id: int) -> dict:
    print(f"Fetching user data for user_id={user_id}")
    time.sleep(1)
    return {
        "id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": datetime.now().isoformat()
    }


def main():
    print("=== Caching System Example ===\n")

    print("--- SQLite Cache Backend ---")
    sqlite_cache = CacheManager(sqbooster.sqlite())

    print("Setting cache values...")
    sqlite_cache.set("user:123", {"name": "Alice", "age": 30}, ttl=10)
    sqlite_cache.set("config:app", {"theme": "dark", "lang": "en"}, ttl=60)

    print("Getting cache values...")
    user_data = sqlite_cache.get("user:123")
    config_data = sqlite_cache.get("config:app")
    print(f"User data: {user_data}")
    print(f"Config data: {config_data}")

    print("\nCache statistics:")
    user_stats = sqlite_cache.get_stats("user:123")
    print(f"User cache stats: {user_stats}")

    print("\n--- JSON Cache Backend ---")
    import tempfile, os
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    json_cache = CacheManager(sqbooster.json(tmp.name))

    print("\n--- Function Caching ---")

    cached_computation = cache_decorator(json_cache, ttl=30, namespace="math")(expensive_computation)
    cached_user_fetch = cache_decorator(json_cache, ttl=60, namespace="api")(fetch_user_data)

    print("First calls (should be slow):")
    result1 = cached_computation(100)
    user1 = cached_user_fetch(123)
    print(f"Computation result: {result1}")
    print(f"User data: {user1}")

    print("\nSecond calls (should be fast):")
    result2 = cached_computation(100)
    user2 = cached_user_fetch(123)
    print(f"Computation result: {result2}")
    print(f"User data: {user2}")

    print("\n--- Namespace-based Caching ---")

    json_cache.set("temp_data", "This is temporary", ttl=5, namespace="temp")
    json_cache.set("temp_data", "This is permanent", ttl=3600, namespace="permanent")

    print("Temporary data:", json_cache.get("temp_data", "temp"))
    print("Permanent data:", json_cache.get("temp_data", "permanent"))

    print("\nWaiting 6 seconds for temporary data to expire...")
    time.sleep(6)

    print("After expiration:")
    print("Temporary data:", json_cache.get("temp_data", "temp"))
    print("Permanent data:", json_cache.get("temp_data", "permanent"))

    print("\n--- Performance Comparison ---")

    start_time = time.time()
    for i in range(3):
        expensive_computation(50)
    no_cache_time = time.time() - start_time

    start_time = time.time()
    for i in range(3):
        cached_computation(50)
    with_cache_time = time.time() - start_time

    print(f"Without cache: {no_cache_time:.2f} seconds")
    print(f"With cache: {with_cache_time:.2f} seconds")
    print(f"Speed improvement: {no_cache_time / with_cache_time:.2f}x")

    os.unlink(tmp.name)
    print("\nCaching system example completed!")


if __name__ == "__main__":
    main()
