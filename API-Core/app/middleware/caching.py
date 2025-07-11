"""
Caching middleware for improved performance.
"""
import json
import logging
from functools import wraps
from flask import request, current_app, g
import hashlib
import time

logger = logging.getLogger(__name__)

class CacheManager:
    """Simple in-memory cache manager."""
    
    def __init__(self):
        self.cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    def get(self, key):
        """Get value from cache."""
        if key in self.cache:
            entry = self.cache[key]
            if entry['expires'] > time.time():
                self.cache_stats['hits'] += 1
                logger.debug(f"Cache hit for key: {key}")
                return entry['value']
            else:
                # Expired entry
                del self.cache[key]
        
        self.cache_stats['misses'] += 1
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    def set(self, key, value, timeout=300):
        """Set value in cache with timeout."""
        self.cache[key] = {
            'value': value,
            'expires': time.time() + timeout,
            'created': time.time()
        }
        logger.debug(f"Cache set for key: {key}, timeout: {timeout}s")
    
    def delete(self, key):
        """Delete key from cache."""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted for key: {key}")
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_stats(self):
        """Get cache statistics."""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (
            self.cache_stats['hits'] / total_requests * 100
            if total_requests > 0 else 0
        )
        
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'total_entries': len(self.cache)
        }
    
    def cleanup_expired(self):
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry['expires'] <= current_time
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache manager instance
cache_manager = CacheManager()


def cached(timeout=300, key_prefix=''):
    """Decorator to cache function results."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(f.__name__, key_prefix, args, kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            
            return result
        
        return decorated_function
    return decorator


def cache_route(timeout=300, key_func=None):
    """Decorator to cache route responses."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func()
            else:
                cache_key = _generate_route_cache_key()
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute route and cache result
            result = f(*args, **kwargs)
            
            # Only cache successful responses
            if hasattr(result, 'status_code') and result.status_code == 200:
                cache_manager.set(cache_key, result, timeout)
            elif isinstance(result, (dict, list)):
                cache_manager.set(cache_key, result, timeout)
            
            return result
        
        return decorated_function
    return decorator


def invalidate_cache_pattern(pattern):
    """Invalidate cache entries matching pattern."""
    keys_to_delete = [
        key for key in cache_manager.cache.keys()
        if pattern in key
    ]
    
    for key in keys_to_delete:
        cache_manager.delete(key)
    
    logger.info(f"Invalidated {len(keys_to_delete)} cache entries matching pattern: {pattern}")


def _generate_cache_key(func_name, prefix, args, kwargs):
    """Generate cache key for function call."""
    # Create a string representation of arguments
    args_str = str(args) + str(sorted(kwargs.items()))
    
    # Create hash of arguments
    args_hash = hashlib.md5(args_str.encode()).hexdigest()
    
    return f"{prefix}:{func_name}:{args_hash}"


def _generate_route_cache_key():
    """Generate cache key for route."""
    # Include method, path, and query parameters
    key_parts = [
        request.method,
        request.path,
        request.query_string.decode()
    ]
    
    # Add user context if available
    if hasattr(g, 'current_user') and g.current_user:
        key_parts.append(str(g.current_user.id))
    
    key_string = '|'.join(key_parts)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    
    return f"route:{key_hash}"