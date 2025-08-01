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
        winRateThreshold = request.args.get('win_rate_threshold', type=float, default=None)
        
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
                minWalletPnl=minWalletPnl,
                winRateThreshold=winRateThreshold
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
        sort_by = request.args.get('sort_by', 'totalPnl')
        sort_order = request.args.get('sort_order', 'desc')
        
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
                days=days,
                sort_by=sort_by,
                sort_order=sort_order
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

@smart_money_pnl_report_bp.route('/api/reports/smartmoneypnl/token/<token_id>', methods=['GET', 'OPTIONS'])
def get_token_investors_pnl(token_id):
    """Get PNL data for wallets that have invested in a specific token."""
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
            
        logger.info(f"Fetching token investors PNL data for token {token_id} over {days} days")
        
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
                
            # Get token investors PNL data
            token_investors_data = handler.getTokenInvestorsPNL(
                token_id=token_id,
                days=days,
                limit=limit,
                sortBy=sortBy,
                sortOrder=sortOrder,
                minTotalPnl=minTotalPnl,
                minWalletPnl=minWalletPnl
            )
            
            if not token_investors_data or (token_investors_data.get('wallets', []) == [] and 'error' in token_investors_data):
                logger.warning(f"No investors found for token {token_id} or an error occurred")
                if 'error' in token_investors_data:
                    response = jsonify({
                        'error': 'Internal server error',
                        'message': token_investors_data['error']
                    })
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response, 500
            
            response = jsonify(token_investors_data)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        logger.error(f"Error fetching token investors PNL data: {str(e)}")
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@smart_money_pnl_report_bp.route('/api/reports/smartmoneypnl/wallet/<wallet_address>/token/<token_address>', methods=['GET', 'OPTIONS'])
def get_wallet_token_details(wallet_address, token_address):
    """Get detailed token movement data for a specific token in a wallet (similar to SmartMoneyMovements API)."""
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
            
        logger.info(f"Fetching token details for wallet {wallet_address} and token {token_address} over {days} days")
        
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
                
            # Get wallet details first
            wallet_details = handler.getWalletPNLDetails(
                wallet_address=wallet_address,
                days=days
            )
            
            if not wallet_details or not wallet_details.get('tokens'):
                logger.warning(f"No PNL details found for wallet {wallet_address}")
                response = jsonify({
                    'error': 'Not found', 
                    'message': f"No token data found for wallet {wallet_address}"
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
            
            # Filter for the specific token
            token_data = None
            for token in wallet_details['tokens']:
                if token['tokenAddress'].lower() == token_address.lower():
                    token_data = token
                    break
            
            if not token_data:
                response = jsonify({
                    'error': 'Not found',
                    'message': f"Token {token_address} not found in wallet {wallet_address} for the specified period"
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 404
            
            # Format response similar to SmartMoneyMovements API
            result = {
                'wallet': {
                    'walletAddress': wallet_address,
                    'totalInvested': wallet_details['wallet']['totalInvested'],
                    'totalTakenOut': wallet_details['wallet']['totalTakenOut'],
                    'totalRemainingValue': wallet_details['wallet']['totalRemainingValue'],
                    'totalRealizedPnl': wallet_details['wallet']['totalRealizedPnl'],
                    'totalPnl': wallet_details['wallet']['totalPnl'],
                    'totalPnlPercentage': wallet_details['wallet']['totalPnlPercentage']
                },
                'token': token_data,
                'period': wallet_details['period'],
                'metrics': wallet_details['metrics']
            }
            
            response = jsonify(result)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        logger.error(f"Error fetching wallet token details: {str(e)}")
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
