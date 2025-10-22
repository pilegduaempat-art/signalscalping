# utils/cache.py
"""
Simple caching to reduce API calls
"""
import time
from functools import wraps

_cache = {}
_cache_timestamps = {}
DEFAULT_TTL = 60  # seconds


def cached(ttl=DEFAULT_TTL):
    """
    Decorator to cache function results
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{args}:{sorted(kwargs.items())}"
            
            # Check if cached and not expired
            now = time.time()
            if cache_key in _cache:
                timestamp = _cache_timestamps.get(cache_key, 0)
                if now - timestamp < ttl:
                    return _cache[cache_key]
            
            # Call function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = now
            
            return result
        return wrapper
    return decorator


def clear_cache():
    """Clear all cached data"""
    global _cache, _cache_timestamps
    _cache = {}
    _cache_timestamps = {}
