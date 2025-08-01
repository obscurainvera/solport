"""
Enterprise-grade caching system for Smart Money PNL Reports.

This module provides a production-ready, thread-safe, configurable caching layer
with metrics, monitoring, and graceful degradation capabilities.

Author: Smart Money Analytics Team
Version: 1.0.0
"""

import time
import threading
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from cachetools import TTLCache, LRUCache
from dataclasses import dataclass
from enum import Enum
import os


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
            report_cache_size=int(os.getenv('CACHE_REPORT_SIZE', '1000')),
            report_cache_ttl=int(os.getenv('CACHE_REPORT_TTL', '3600')),
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
        
        # Initialize caches
        self._token_cache = TTLCache(
            maxsize=self.config.token_cache_size,
            ttl=self.config.token_cache_ttl
        )
        self._report_cache = TTLCache(
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
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        Generate a deterministic cache key from parameters.
        
        Args:
            prefix: Cache key prefix (e.g., 'token_price', 'report_pnl')
            **kwargs: Key-value pairs to include in the key
            
        Returns:
            str: Generated cache key
        """
        # Sort kwargs for consistent key generation
        sorted_params = sorted(kwargs.items())
        key_data = f"{prefix}_{json.dumps(sorted_params, sort_keys=True)}"
        
        # Use hash for long keys to prevent key length issues
        if len(key_data) > self.config.max_key_length:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{prefix}_{key_hash}"
        
        return key_data.replace(' ', '').replace(',', '_').replace(':', '_')
    
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
        
        try:
            with self._cache_lock:
                cached_report = self._report_cache.get(cache_key)
                
                if cached_report is not None:
                    response_time = (time.time() - start_time) * 1000
                    self._update_metrics(self._report_metrics, hit=True, response_time_ms=response_time)
                    self.logger.info(f"Report cache HIT: {cache_key} ({response_time:.1f}ms)")
                    return cached_report
                
                # Generate new report
                self.logger.info(f"Report cache MISS: {cache_key}")
                report_data = generate_func()
                
                # Cache the result
                self._report_cache[cache_key] = report_data
                
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