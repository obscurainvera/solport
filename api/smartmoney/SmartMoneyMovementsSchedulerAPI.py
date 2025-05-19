from flask import Blueprint, jsonify, request, make_response
from scheduler.SmartMoneyMovementsScheduler import SmartMoneyMovementsScheduler
from logs.logger import get_logger
import time

logger = get_logger(__name__)

# Create a Blueprint for smart money movements scheduler endpoints
smart_money_movements_scheduler_bp = Blueprint('smart_money_movements_scheduler', __name__)

# Add CORS headers to all responses
@smart_money_movements_scheduler_bp.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    # Clear any existing CORS headers to prevent duplicates
    response.headers.pop('Access-Control-Allow-Origin', None)
    response.headers.pop('Access-Control-Allow-Headers', None)
    response.headers.pop('Access-Control-Allow-Methods', None)
    
    # Add CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept, Origin, Referer, User-Agent, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    return response

@smart_money_movements_scheduler_bp.route('/api/smartmoneymovements/scheduler/run', methods=['POST', 'OPTIONS'])
def handleSmartMoneyMovements():
    """Run the smart money movements scheduler manually"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        return make_response(jsonify({}), 200)
    
    try:
        start_time = time.time()
        
        # Get PnL threshold from request or use default
        data = request.get_json() or {}
        pnl_threshold = float(data.get('pnl_threshold', 100000))
        
        logger.info(f"Starting smart money movements scheduler with PnL threshold: {pnl_threshold}")
        
        # Initialize and run the scheduler
        scheduler = SmartMoneyMovementsScheduler()
        result = scheduler.handleSmartMoneyMovementsUpdate(pnl_threshold)
        
        # Add execution time
        execution_time = time.time() - start_time
        result['totalExecutionTime'] = f"{execution_time:.2f}s"
        
        logger.info(f"Smart money movements scheduler completed in {execution_time:.2f} seconds")
        
        return jsonify({
            'success': True,
            'message': f"Successfully processed {result['walletsProcessed']} wallets with PnL > {pnl_threshold}",
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Error running smart money movements scheduler: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
