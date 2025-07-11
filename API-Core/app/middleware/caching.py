"""Caching middleware and utilities."""

from flask import current_app, request, jsonify
from functools import wraps
import hashlib
import json
import redis
from typing import Optional, Any, Dict
import pickle


class CacheManager:
    """Redis-based cache manager for application data."""
    
    def __init__(self, app=None):
        self.redis_client = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize cache with Flask app."""
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=False)
            # Test connection
            self.redis_client.ping()
            app.logger.info("Redis cache connected successfully")
        except Exception as e:
            app.logger.warning(f"Redis cache unavailable: {e}")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data:
                return pickle.loads(data)
        except Exception as e:
            current_app.logger.error(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Set value in cache with timeout."""
        if not self.redis_client:
            return False
        
        try:
            serialized = pickle.dumps(value)
            return self.redis_client.setex(key, timeout, serialized)
        except Exception as e:
            current_app.logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            current_app.logger.error(f"Cache delete error: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern."""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
        except Exception as e:
            current_app.logger.error(f"Cache clear pattern error: {e}")
        return 0


# Global cache instance
cache_manager = CacheManager()


def cached(timeout: int = 300, key_prefix: str = None):
    """Decorator to cache function results."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            if key_prefix:
                cache_key = f"{key_prefix}:"
            else:
                cache_key = f"{f.__module__}.{f.__name__}:"
            
            # Include function arguments in key
            key_data = {
                'args': args,
                'kwargs': kwargs,
                'endpoint': request.endpoint if request else None
            }
            key_hash = hashlib.md5(json.dumps(key_data, sort_keys=True, default=str).encode()).hexdigest()
            cache_key += key_hash
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                current_app.logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            current_app.logger.debug(f"Cache set for key: {cache_key}")
            
            return result
        return decorated_function
    return decorator


def cache_invalidate_pattern(pattern: str):
    """Invalidate cache entries matching pattern."""
    return cache_manager.clear_pattern(pattern)