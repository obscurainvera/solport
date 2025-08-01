"""
Cache Monitoring API for Smart Money PNL Reports.

Provides endpoints for cache metrics, health checks, and management.
"""

from flask import Blueprint, jsonify, request
from cache import cache_manager
from logs.logger import get_logger
import time

logger = get_logger(__name__)

cache_monitoring_bp = Blueprint('cache_monitoring', __name__)


@cache_monitoring_bp.route('/api/cache/metrics', methods=['GET', 'OPTIONS'])
def get_cache_metrics():
    """Get comprehensive cache performance metrics."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
    
    try:
        metrics = cache_manager.get_metrics()
        
        response = jsonify({
            'status': 'success',
            'data': metrics,
            'timestamp': time.time()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Error fetching cache metrics: {str(e)}")
        response = jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@cache_monitoring_bp.route('/api/cache/health', methods=['GET', 'OPTIONS'])
def get_cache_health():
    """Perform cache health check."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
    
    try:
        health_status = cache_manager.health_check()
        
        status_code = 200 if health_status['status'] == 'healthy' else 503
        
        response = jsonify({
            'status': 'success',
            'data': health_status,
            'timestamp': time.time()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, status_code
        
    except Exception as e:
        logger.error(f"Error performing cache health check: {str(e)}")
        response = jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@cache_monitoring_bp.route('/api/cache/clear', methods=['POST', 'OPTIONS'])
def clear_cache():
    """Clear cache contents."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
    
    try:
        # Get cache type from request body
        data = request.get_json() or {}
        cache_type = data.get('cache_type', 'all')  # all, token, report
        
        if cache_type not in ['all', 'token', 'report']:
            response = jsonify({
                'status': 'error',
                'error': 'Invalid cache_type. Must be: all, token, or report',
                'timestamp': time.time()
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        cache_manager.clear_cache(cache_type)
        
        response = jsonify({
            'status': 'success',
            'message': f'{cache_type.title()} cache cleared successfully',
            'timestamp': time.time()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        response = jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@cache_monitoring_bp.route('/api/cache/dashboard', methods=['GET', 'OPTIONS'])
def get_cache_dashboard():
    """Get cache dashboard data with performance insights."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
    
    try:
        metrics = cache_manager.get_metrics()
        health = cache_manager.health_check()
        
        # Calculate performance insights
        token_cache = metrics['token_cache']
        report_cache = metrics['report_cache']
        
        # Efficiency analysis
        token_efficiency = "Excellent" if token_cache['hit_rate'] > 80 else \
                          "Good" if token_cache['hit_rate'] > 60 else \
                          "Needs Improvement" if token_cache['hit_rate'] > 40 else "Poor"
        
        report_efficiency = "Excellent" if report_cache['hit_rate'] > 90 else \
                           "Good" if report_cache['hit_rate'] > 70 else \
                           "Needs Improvement" if report_cache['hit_rate'] > 50 else "Poor"
        
        # Memory usage analysis
        token_memory_usage = (token_cache['current_size'] / token_cache['max_size']) * 100
        report_memory_usage = (report_cache['current_size'] / report_cache['max_size']) * 100
        
        dashboard_data = {
            'overview': {
                'status': health['status'],
                'total_requests': token_cache['total_requests'] + report_cache['total_requests'],
                'total_hits': token_cache['hits'] + report_cache['hits'],
                'overall_hit_rate': round(
                    ((token_cache['hits'] + report_cache['hits']) / 
                     max(token_cache['total_requests'] + report_cache['total_requests'], 1)) * 100, 2
                )
            },
            'performance': {
                'token_cache_efficiency': token_efficiency,
                'report_cache_efficiency': report_efficiency,
                'avg_response_time_ms': round(
                    (token_cache['avg_response_time_ms'] + report_cache['avg_response_time_ms']) / 2, 2
                )
            },
            'memory': {
                'token_cache_usage_percent': round(token_memory_usage, 1),
                'report_cache_usage_percent': round(report_memory_usage, 1),
                'total_entries': token_cache['current_size'] + report_cache['current_size']
            },
            'detailed_metrics': metrics,
            'health_check': health,
            'recommendations': []
        }
        
        # Add recommendations based on metrics
        if token_cache['hit_rate'] < 60:
            dashboard_data['recommendations'].append(
                "Consider increasing token cache TTL or size for better hit rates"
            )
        
        if report_cache['hit_rate'] < 70:
            dashboard_data['recommendations'].append(
                "Report cache hit rate is low - check if parameters are varying too much"
            )
        
        if token_memory_usage > 90:
            dashboard_data['recommendations'].append(
                "Token cache is near capacity - consider increasing max size"
            )
        
        if token_cache['errors'] > 0 or report_cache['errors'] > 0:
            dashboard_data['recommendations'].append(
                "Cache errors detected - check logs for API failures"
            )
        
        response = jsonify({
            'status': 'success',
            'data': dashboard_data,
            'timestamp': time.time()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Error generating cache dashboard: {str(e)}")
        response = jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': time.time()
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500