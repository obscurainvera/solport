from flask import Blueprint, jsonify, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.smartmoneypnl.SmartMoneyPNLReportHandler import SmartMoneyPNLReportHandler
from logs.logger import get_logger
import time

logger = get_logger(__name__)

smart_money_pnl_report_bp = Blueprint('smart_money_pnl_report', __name__)

@smart_money_pnl_report_bp.route('/api/reports/smartmoneypnl', methods=['GET', 'OPTIONS'])
def get_smart_money_pnl_report():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get query parameters with defaults
        days = request.args.get('days', type=int, default=30)
        limit = request.args.get('limit', type=int, default=100)
        sortBy = request.args.get('sort_by', 'pnl')
        sortOrder = request.args.get('sort_order', 'desc')
        
        # Get filter parameters
        minTotalPnl = request.args.get('min_total_pnl', type=float, default=None)
        minWalletPnl = request.args.get('min_wallet_pnl', type=float, default=None)
        
        # Validate days parameter - only allow 7, 30, or 90 days
        if days not in [7, 30, 90]:
            days = 30
            logger.warning(f"Invalid days parameter: {days}, defaulting to 30")
            
        logger.info(f"Generating smart money PNL report for {days} days")
        
        # Use the handler to get the data
        with SQLitePortfolioDB() as db:
            handler = SmartMoneyPNLReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'smart_money_pnl_report' not found")
                response = jsonify({
                    'error': 'Configuration error',
                    'message': "Handler 'smart_money_pnl_report' not found"
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
                
            start_time = time.time()
            
            # Get the report data
            report_data = handler.getTopPNLWallets(
                days=days,
                limit=limit,
                sortBy=sortBy,
                sortOrder=sortOrder,
                minTotalPnl=minTotalPnl,
                minWalletPnl=minWalletPnl
            )
            
            end_time = time.time()
            logger.info(f"Generated smart money PNL report in {end_time - start_time:.2f} seconds")

        # Create response with proper CORS headers
        response = jsonify(report_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        logger.error(f"Error in smart money PNL report API: {str(e)}")
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@smart_money_pnl_report_bp.route('/api/reports/smartmoneypnl/wallet/<wallet_address>', methods=['GET', 'OPTIONS'])
def get_wallet_pnl_details(wallet_address):
    """Get detailed PNL data for a specific wallet."""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get query parameters with defaults
        days = request.args.get('days', type=int, default=30)
        
        # Validate days parameter - only allow 7, 30, or 90 days
        if days not in [7, 30, 90]:
            days = 30
            logger.warning(f"Invalid days parameter: {days}, defaulting to 30")
            
        logger.info(f"Fetching wallet PNL details for wallet {wallet_address} over {days} days")
        
        with SQLitePortfolioDB() as db:
            handler = SmartMoneyPNLReportHandler(db)
            
            if handler is None:
                logger.error("Handler 'smart_money_pnl_report' not found")
                response = jsonify({
                    'error': 'Configuration error',
                    'message': "Handler 'smart_money_pnl_report' not found"
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
                
            # Get wallet details
            wallet_details = handler.getWalletPNLDetails(
                wallet_address=wallet_address,
                days=days
            )
            
            if not wallet_details:
                logger.warning(f"No PNL details found for wallet {wallet_address}")
                response = jsonify({
                    'error': 'Not found',
                    'message': f"No PNL details found for wallet {wallet_address}"
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
            
            response = jsonify(wallet_details)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        logger.error(f"Error fetching wallet PNL details: {str(e)}")
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
