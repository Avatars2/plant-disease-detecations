#!/usr/bin/env python3
"""
Cache Manager for Plant Disease Detection
Redis-based caching for improved performance
"""

import redis
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from functools import wraps
import os
from dotenv import load_dotenv

load_dotenv()

class CacheManager:
    def __init__(self):
        self.redis_client = None
        self.cache_enabled = True
        self.default_ttl = 3600  # 1 hour
        self.memory_cache = {}
        self.memory_cache_size = 1000  # Limit memory cache size
        
        # Initialize Redis connection
        self.init_redis()
    
    def init_redis(self):
        """Initialize Redis connection"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=False,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            
            # Test connection
            self.redis_client.ping()
            print("✅ Redis cache initialized successfully")
            
        except Exception as e:
            print(f"⚠️ Redis not available, using memory cache: {e}")
            self.redis_client = None
            self.memory_cache = {}
    
    def generate_cache_key(self, prefix, *args, **kwargs):
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': sorted(kwargs.items())
        }
        key_string = json.dumps(key_data, sort_keys=True)
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key):
        """Get value from cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value:
                    return pickle.loads(value)
            else:
                # Memory cache fallback
                if key in self.memory_cache:
                    item = self.memory_cache[key]
                    if datetime.now() < item['expires']:
                        return item['value']
                    else:
                        del self.memory_cache[key]
            return None
        except Exception as e:
            print(f"❌ Cache get error: {e}")
            return None
    
    def set(self, key: str, value, ttl: int = None) -> bool:
        """Set cache value with optimized memory management"""
        if not self.cache_enabled:
            return False
        
        ttl = ttl or self.default_ttl
        
        try:
            if self.redis_client:
                # Use Redis if available
                serialized_value = pickle.dumps(value)
                self.redis_client.setex(key, ttl, serialized_value)
            else:
                # Use memory cache with size limit
                if len(self.memory_cache) >= self.memory_cache_size:
                    # Remove oldest entry (simple FIFO)
                    oldest_key = next(iter(self.memory_cache))
                    del self.memory_cache[oldest_key]
                
                expires = datetime.now() + timedelta(seconds=ttl)
                self.memory_cache[key] = {
                    'value': value,
                    'expires': expires
                }
            return True
        except Exception as e:
            print(f"❌ Cache set error: {e}")
            return False
    
    def delete(self, key):
        """Delete key from cache"""
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                if key in self.memory_cache:
                    del self.memory_cache[key]
            return True
        except Exception as e:
            print(f"❌ Cache delete error: {e}")
            return False
    
    def clear(self, pattern=None):
        """Clear cache"""
        try:
            if self.redis_client:
                if pattern:
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                else:
                    self.redis_client.flushdb()
            else:
                if pattern:
                    keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
                    for key in keys_to_delete:
                        del self.memory_cache[key]
                else:
                    self.memory_cache.clear()
            return True
        except Exception as e:
            print(f"❌ Cache clear error: {e}")
            return False
    
    def cache_stats(self):
        """Get cache statistics"""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    'type': 'redis',
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0)
                }
            else:
                return {
                    'type': 'memory',
                    'cache_size': len(self.memory_cache),
                    'max_memory': 'N/A'
                }
        except Exception as e:
            print(f"❌ Cache stats error: {e}")
            return {'error': str(e)}

# Global cache instance
cache_manager = CacheManager()

def cache_result(prefix, ttl=None):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_manager.generate_cache_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate cache keys matching pattern"""
    return cache_manager.clear(pattern)

# Prediction-specific caching functions
def cache_prediction_result(image_hash, prediction_result, ttl=3600):
    """Cache prediction result"""
    cache_key = f"prediction:{image_hash}"
    return cache_manager.set(cache_key, prediction_result, ttl)

def get_cached_prediction(image_hash):
    """Get cached prediction result"""
    cache_key = f"prediction:{image_hash}"
    return cache_manager.get(cache_key)

def cache_user_history(user_id, history_data, ttl=1800):
    """Cache user history"""
    cache_key = f"history:{user_id}"
    return cache_manager.set(cache_key, history_data, ttl)

def get_cached_user_history(user_id):
    """Get cached user history"""
    cache_key = f"history:{user_id}"
    return cache_manager.get(cache_key)

def cache_model_classes(classes_data, ttl=86400):
    """Cache model classes"""
    cache_key = "model:classes"
    return cache_manager.set(cache_key, classes_data, ttl)

def get_cached_model_classes():
    """Get cached model classes"""
    cache_key = "model:classes"
    return cache_manager.get(cache_key)

# Performance monitoring
def monitor_cache_performance():
    """Monitor cache performance"""
    stats = cache_manager.cache_stats()
    print("📊 Cache Performance Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    return stats

if __name__ == "__main__":
    # Test cache functionality
    print("🧪 Testing cache functionality...")
    
    # Test basic operations
    test_key = "test:key"
    test_value = {"message": "Hello World", "timestamp": datetime.now().isoformat()}
    
    # Set and get
    if cache_manager.set(test_key, test_value, 60):
        retrieved = cache_manager.get(test_key)
        if retrieved and retrieved['message'] == test_value['message']:
            print("✅ Cache test passed")
        else:
            print("❌ Cache test failed")
    
    # Show stats
    monitor_cache_performance()
