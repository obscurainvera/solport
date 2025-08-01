"""
Smart Money PNL Reports - Enterprise Caching System

This package provides production-ready caching capabilities with:
- Thread-safe operations
- Performance metrics and monitoring
- Configurable TTL and size limits
- Graceful degradation
- Health checks and diagnostics

Usage:
    from cache import cache_manager
    
    # Token price caching
    prices = cache_manager.get_token_prices(tokens, fetch_function)
    
    # Report caching
    report = cache_manager.get_report(params, generate_function)
    
    # Metrics and monitoring
    metrics = cache_manager.get_metrics()
"""

from .cache_manager import CacheManager, CacheConfig, CacheType, cache_manager

__version__ = "1.0.0"
__all__ = ["CacheManager", "CacheConfig", "CacheType", "cache_manager"]