"""
Enterprise-grade caching system for Smart Money PNL Reports.

This module provides a production-ready, thread-safe, configurable caching layer
with metrics, monitoring, and graceful degradation capabilities.

RECENT UPDATES:
• Fixed cache key generation to properly differentiate filter parameters
• Added parameter normalization (None → "null", consistent data type handling)
• Enhanced logging and debugging capabilities
• Automatic cache clearing on initialization due to key format changes
• Replaced cachetools dependency with built-in SimpleTTLCache implementation
• Added cache clear API endpoint for manual cache management
• Result: Different API filter combinations now create unique cache entries

Author: Smart Money Analytics Team
Version: 1.1.0
"""

import time
import threading
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import os


class SimpleTTLCache:
    """Simple TTL Cache implementation without external dependencies."""
    
    def __init__(self, maxsize: int, ttl: int):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.RLock()
    
    def _is_expired(self, key: str) -> bool:
        """Check if a cache entry is expired."""
        if key not in self._timestamps:
            return True
        return time.time() - self._timestamps[key] > self.ttl
    
    def _cleanup_expired(self):
        """Remove expired entries."""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self._timestamps.items()
            if current_time - timestamp > self.ttl
        ]
        for key in expired_keys:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
    
    def _enforce_size_limit(self):
        """Remove oldest entries if cache exceeds size limit."""
        while len(self._cache) > self.maxsize:
            # Remove oldest entry
            oldest_key = min(self._timestamps.keys(), key=self._timestamps.get)
            self._cache.pop(oldest_key, None)
            self._timestamps.pop(oldest_key, None)
    
    def get(self, key: str) -> Any:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache or self._is_expired(key):
                return None
            return self._cache[key]
    
    def __setitem__(self, key: str, value: Any):
        """Set value in cache."""
        with self._lock:
            self._cleanup_expired()
            self._cache[key] = value
            self._timestamps[key] = time.time()
            self._enforce_size_limit()
    
    def __getitem__(self, key: str) -> Any:
        """Get item using bracket notation."""
        return self.get(key)
    
    def __len__(self) -> int:
        """Get cache size."""
        with self._lock:
            self._cleanup_expired()
            return len(self._cache)
    
    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
    
    def keys(self) -> List[str]:
        """Get all cache keys."""
        with self._lock:
            self._cleanup_expired()
            return list(self._cache.keys())
    
    def pop(self, key: str, default=None) -> Any:
        """Remove and return value from cache."""
        with self._lock:
            self._timestamps.pop(key, None)
            return self._cache.pop(key, default)


class CacheType(Enum):
    """Cache type enumeration."""
    MEMORY = "memory"
    REDIS = "redis"  # Future implementation
    HYBRID = "hybrid"  # Future implementation


@dataclass
class CacheConfig:
    """Cache configuration settings."""
    # Token price cache settings
    token_cache_size: int = 10000
    token_cache_ttl: int = 3600  # 1 hour
    
    # Report cache settings
    report_cache_size: int = 1000
    report_cache_ttl: int = 3600  # 1 hour
    
    # General settings
    cache_type: CacheType = CacheType.MEMORY
    enable_metrics: bool = True
    enable_compression: bool = False
    max_key_length: int = 250
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Load configuration from environment variables."""
        return cls(
            token_cache_size=int(os.getenv('CACHE_TOKEN_SIZE', '10000')),
            token_cache_ttl=int(os.getenv('CACHE_TOKEN_TTL', '3600')),
            report_cache_size=int(os.getenv('CACHE_REPORT_SIZE', '10000')),
            report_cache_ttl=int(os.getenv('CACHE_REPORT_TTL', '36000')),
            enable_metrics=os.getenv('CACHE_ENABLE_METRICS', 'true').lower() == 'true',
            enable_compression=os.getenv('CACHE_ENABLE_COMPRESSION', 'false').lower() == 'true'
        )


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    errors: int = 0
    total_requests: int = 0
    avg_response_time_ms: float = 0.0
    cache_size: int = 0
    last_reset: datetime = None
    
    def __post_init__(self):
        if self.last_reset is None:
            self.last_reset = datetime.now()
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits / self.total_requests) * 100
    
    def reset(self):
        """Reset all metrics."""
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.errors = 0
        self.total_requests = 0
        self.avg_response_time_ms = 0.0
        self.last_reset = datetime.now()


class CacheManager:
    """
    Production-ready cache manager with thread-safety, metrics, and monitoring.
    
    Features:
    - Thread-safe operations with RLock
    - Configurable TTL and size limits
    - Performance metrics and monitoring
    - Graceful degradation on failures
    - Memory-efficient key generation
    - Production logging
    """
    
    _instance = None
    _lock = threading.RLock()
    
    def __new__(cls, config: Optional[CacheConfig] = None):
        """Singleton pattern for global cache instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CacheManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """Initialize cache manager with configuration."""
        if self._initialized:
            return
            
        self.config = config or CacheConfig.from_env()
        self.logger = logging.getLogger(__name__)
        
        # Initialize caches with simple TTL implementation
        self._token_cache = SimpleTTLCache(
            maxsize=self.config.token_cache_size,
            ttl=self.config.token_cache_ttl
        )
        self._report_cache = SimpleTTLCache(
            maxsize=self.config.report_cache_size,
            ttl=self.config.report_cache_ttl
        )
        
        # Thread safety
        self._cache_lock = threading.RLock()
        
        # Metrics
        self._token_metrics = CacheMetrics()
        self._report_metrics = CacheMetrics()
        
        self._initialized = True
        self.logger.info(f"CacheManager initialized with config: {self.config}")
        
        # Clear cache on initialization due to updated key format
        self.logger.info("Clearing cache due to updated cache key format")
        self.clear_cache("all")
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a deterministic cache key from parameters.
        
        CACHE KEY FIX IMPLEMENTED:
        • Problem: Same cache key generated for different filter combinations
        • Root cause: None values and parameter variations not properly differentiated
        • Solution implemented:
          1. Convert None to explicit "null" string (not empty/missing)
          2. Normalize all data types (bool, int, float, str) to consistent strings
          3. Create detailed parameter string with key=value pairs
          4. Sort parameters alphabetically for consistency
          5. Generate filesystem-safe cache key with all parameter info
        • Result: Different API calls with different filters now create unique cache entries
        • Examples:
          - No filters: report_days_30_minTotalPnl_null_winRateThreshold_null
          - With filters: report_days_30_minTotalPnl_1000.0_winRateThreshold_10000.0
        
        Args:
            prefix: Cache key prefix (e.g., 'token_price', 'report_pnl')
            **kwargs: Key-value pairs to include in the key
            
        Returns:
            str: Generated cache key with all parameters properly differentiated
        """
        # Clean and normalize parameters for consistent key generation
        normalized_params = {}
        for key, value in kwargs.items():
            # Convert None to a string representation to differentiate from missing keys
            if value is None:
                normalized_params[key] = "null"
            # Convert boolean values to consistent strings
            elif isinstance(value, bool):
                normalized_params[key] = "true" if value else "false"
            # Convert numeric values to strings with consistent formatting
            elif isinstance(value, (int, float)):
                normalized_params[key] = str(value)
            # Keep strings as-is but ensure they're clean
            elif isinstance(value, str):
                normalized_params[key] = value.strip()
            else:
                # For other types, convert to string
                normalized_params[key] = str(value)
        
        # Sort parameters for consistent key generation
        sorted_params = sorted(normalized_params.items())
        
        # Create a more detailed key that includes all parameter information
        param_string = "&".join([f"{k}={v}" for k, v in sorted_params])
        key_data = f"{prefix}#{param_string}"
        
        # Use hash for long keys to prevent key length issues
        if len(key_data) > self.config.max_key_length:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            final_key = f"{prefix}_{key_hash}"
            self.logger.debug(f"Generated hashed cache key: {final_key} (original: {key_data[:100]}...)")
            return final_key
        
        # Make key filesystem/cache-safe
        final_key = key_data.replace(' ', '').replace(',', '_').replace(':', '_').replace('#', '_').replace('&', '_').replace('=', '_')
        self.logger.debug(f"Generated cache key: {final_key}")
        return final_key
    
    def _update_metrics(self, metrics: CacheMetrics, hit: bool, response_time_ms: float):
        """Update cache metrics."""
        if not self.config.enable_metrics:
            return
            
        with self._cache_lock:
            metrics.total_requests += 1
            if hit:
                metrics.hits += 1
            else:
                metrics.misses += 1
            
            # Update average response time
            if metrics.total_requests == 1:
                metrics.avg_response_time_ms = response_time_ms
            else:
                metrics.avg_response_time_ms = (
                    (metrics.avg_response_time_ms * (metrics.total_requests - 1) + response_time_ms) /
                    metrics.total_requests
                )
    
    def get_token_prices(self, token_addresses: List[str], 
                        fetch_func: Callable[[List[str]], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get token prices with intelligent caching.
        
        Args:
            token_addresses: List of token addresses to fetch prices for
            fetch_func: Function to call for fetching uncached prices
            
        Returns:
            Dict[str, Any]: Token address to price data mapping
        """
        start_time = time.time()
        
        try:
            with self._cache_lock:
                cached_results = {}
                uncached_tokens = []
                
                # Check cache for each token
                for token in token_addresses:
                    cache_key = self._generate_cache_key("token_price", address=token)
                    cached_price = self._token_cache.get(cache_key)
                    
                    if cached_price is not None:
                        cached_results[token] = cached_price
                    else:
                        uncached_tokens.append(token)
                
                # All tokens cached - return immediately
                if not uncached_tokens:
                    response_time = (time.time() - start_time) * 1000
                    self._update_metrics(self._token_metrics, hit=True, response_time_ms=response_time)
                    self.logger.info(f"Token cache HIT: {len(token_addresses)} tokens ({response_time:.1f}ms)")
                    return cached_results
                
                # Fetch uncached tokens
                self.logger.info(f"Token cache PARTIAL: {len(cached_results)} cached, {len(uncached_tokens)} fetching")
                new_prices = fetch_func(uncached_tokens)
                
                # Cache new prices
                for token, price_data in new_prices.items():
                    cache_key = self._generate_cache_key("token_price", address=token)
                    self._token_cache[cache_key] = price_data
                
                # Combine results
                cached_results.update(new_prices)
                
                response_time = (time.time() - start_time) * 1000
                hit = len(uncached_tokens) == 0
                self._update_metrics(self._token_metrics, hit=hit, response_time_ms=response_time)
                
                return cached_results
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_metrics(self._token_metrics, hit=False, response_time_ms=response_time)
            self._token_metrics.errors += 1
            self.logger.error(f"Token cache error: {str(e)}")
            
            # Graceful degradation - try to fetch directly
            try:
                return fetch_func(token_addresses)
            except Exception as fallback_error:
                self.logger.error(f"Token fetch fallback failed: {str(fallback_error)}")
                return {}
    
    def get_report(self, cache_key_params: Dict[str, Any], 
                  generate_func: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get report with caching.
        
        Args:
            cache_key_params: Parameters to generate cache key
            generate_func: Function to call for generating uncached report
            
        Returns:
            Dict[str, Any]: Report data
        """
        start_time = time.time()
        cache_key = self._generate_cache_key("report", **cache_key_params)
        
        # Log the parameters being used for cache key generation
        self.logger.info(f"Report cache lookup with params: {cache_key_params}")
        
        try:
            with self._cache_lock:
                cached_report = self._report_cache.get(cache_key)
                
                if cached_report is not None:
                    response_time = (time.time() - start_time) * 1000
                    self._update_metrics(self._report_metrics, hit=True, response_time_ms=response_time)
                    self.logger.info(f"Report cache HIT: {cache_key[:50]}... ({response_time:.1f}ms)")
                    return cached_report
                
                # Generate new report
                self.logger.info(f"Report cache MISS: {cache_key[:50]}... - Generating new report")
                report_data = generate_func()
                
                # Cache the result (but only if it's valid)
                if report_data and not report_data.get('error'):
                    self._report_cache[cache_key] = report_data
                    self.logger.info(f"Report cached successfully: {cache_key[:50]}...")
                else:
                    self.logger.warning(f"Report not cached due to error: {report_data.get('error', 'Unknown error')}")
                
                response_time = (time.time() - start_time) * 1000
                self._update_metrics(self._report_metrics, hit=False, response_time_ms=response_time)
                
                return report_data
                
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self._update_metrics(self._report_metrics, hit=False, response_time_ms=response_time)
            self._report_metrics.errors += 1
            self.logger.error(f"Report cache error: {str(e)}")
            
            # Graceful degradation
            try:
                return generate_func()
            except Exception as fallback_error:
                self.logger.error(f"Report generation fallback failed: {str(fallback_error)}")
                return {"error": "Report generation failed", "wallets": []}
    
    def clear_cache(self, cache_type: str = "all"):
        """
        Clear cache contents.
        
        Args:
            cache_type: "all", "token", or "report"
        """
        with self._cache_lock:
            if cache_type in ("all", "token"):
                self._token_cache.clear()
                self._token_metrics.reset()
                self.logger.info("Token cache cleared")
            
            if cache_type in ("all", "report"):
                self._report_cache.clear()
                self._report_metrics.reset()
                self.logger.info("Report cache cleared")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive cache metrics."""
        with self._cache_lock:
            return {
                "token_cache": {
                    "hits": self._token_metrics.hits,
                    "misses": self._token_metrics.misses,
                    "hit_rate": round(self._token_metrics.hit_rate, 2),
                    "total_requests": self._token_metrics.total_requests,
                    "avg_response_time_ms": round(self._token_metrics.avg_response_time_ms, 2),
                    "errors": self._token_metrics.errors,
                    "current_size": len(self._token_cache),
                    "max_size": self.config.token_cache_size,
                    "ttl_seconds": self.config.token_cache_ttl
                },
                "report_cache": {
                    "hits": self._report_metrics.hits,
                    "misses": self._report_metrics.misses,
                    "hit_rate": round(self._report_metrics.hit_rate, 2),
                    "total_requests": self._report_metrics.total_requests,
                    "avg_response_time_ms": round(self._report_metrics.avg_response_time_ms, 2),
                    "errors": self._report_metrics.errors,
                    "current_size": len(self._report_cache),
                    "max_size": self.config.report_cache_size,
                    "ttl_seconds": self.config.report_cache_ttl
                },
                "config": {
                    "cache_type": self.config.cache_type.value,
                    "metrics_enabled": self.config.enable_metrics,
                    "compression_enabled": self.config.enable_compression
                }
            }
    
    def get_cache_keys(self, cache_type: str = "report") -> List[str]:
        """
        Get all cache keys for debugging purposes.
        
        Args:
            cache_type: "token" or "report"
            
        Returns:
            List[str]: List of cache keys
        """
        with self._cache_lock:
            if cache_type == "token":
                return self._token_cache.keys()
            elif cache_type == "report":
                return self._report_cache.keys()
            else:
                return []
    
    def health_check(self) -> Dict[str, Any]:
        """Perform cache health check."""
        try:
            with self._cache_lock:
                # Test cache operations
                test_key = "health_check_test"
                test_value = {"timestamp": time.time()}
                
                # Test token cache
                self._token_cache[test_key] = test_value
                token_test = self._token_cache.get(test_key) == test_value
                
                # Test report cache
                self._report_cache[test_key] = test_value
                report_test = self._report_cache.get(test_key) == test_value
                
                # Cleanup
                self._token_cache.pop(test_key, None)
                self._report_cache.pop(test_key, None)
                
                return {
                    "status": "healthy" if (token_test and report_test) else "degraded",
                    "token_cache_operational": token_test,
                    "report_cache_operational": report_test,
                    "cache_keys_count": {
                        "token_cache": len(self._token_cache),
                        "report_cache": len(self._report_cache)
                    },
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Global cache instance
cache_manager = CacheManager()