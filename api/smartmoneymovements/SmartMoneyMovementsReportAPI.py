from flask import Blueprint, jsonify, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.smartmoneymovements.SmartMoneyMovementsReportHandler import SmartMoneyMovementsReportHandler
from logs.logger import get_logger

logger = get_logger(__name__)

smartMoneyMovementsReportBp = Blueprint('smart_money_movements_report', __name__)

@smartMoneyMovementsReportBp.route('/api/reports/smartmoneymovements/wallet/<wallet_address>', methods=['GET', 'OPTIONS'])
def getLastNDayInvestmentReport(wallet_address):
    """
    Get smart money movement report for a wallet within a specified time period.
    Shows investment details including total amounts invested/withdrawn, remaining coins,
    current prices, realized PNL, and total PNL with percentage.
    
    Args:
        wallet_address: The wallet address to analyze
        
    Query Parameters:
        days: Number of days to look back (default: 30)
        sort_by: Field to sort tokens by (default: totalPnl)
        sort_order: Sort order (asc or desc)
        
    Returns:
        JSON response with investment report data
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
        
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        sortBy = request.args.get('sort_by', 'totalPnl')
        sortOrder = request.args.get('sort_order', 'desc')
        
        # Validate days parameter
        if days <= 0:
            days = 30
        elif days > 365:
            days = 365  # Limit to one year
        
        # Use the handler to get the report data
        with SQLitePortfolioDB() as db:
            handler = SmartMoneyMovementsReportHandler(db)
            
            report_data = handler.getLastNDaysInvestmentReport(
                wallet_address=wallet_address,
                days=days,
                sort_by=sortBy,
                sort_order=sortOrder
            )
            
            # Return the data
            response = jsonify(report_data)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        logger.error(f"Error in smart money movements report API: {str(e)}")
        response = jsonify({
            'error': 'Server error',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
        
@smartMoneyMovementsReportBp.route('/api/reports/smartmoneymovements/wallet/<wallet_address>/token/<token_address>', methods=['GET', 'OPTIONS'])
def getTokenMovementsForWallet(wallet_address, token_address):
    """
    Get detailed movement data for a specific token in a wallet over a time period.
    
    Args:
        wallet_address: The wallet address to analyze
        token_address: The token address to get movements for
        
    Query Parameters:
        days: Number of days to look back (default: 30)
        
    Returns:
        JSON response with detailed token movement data
    """
    if request.method == 'OPTIONS':
        # Handle preflight request
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response
        
    try:
        # Get query parameters
        days = request.args.get('days', 30, type=int)
        
        # Validate days parameter
        if days <= 0:
            days = 30
        elif days > 365:
            days = 365  # Limit to one year
        
        # Use the handler to get the token movement data
        with SQLitePortfolioDB() as db:
            handler = SmartMoneyMovementsReportHandler(db)
            
            token_data = handler.getTokenMovementsForWallet(
                wallet_address=wallet_address,
                token_address=token_address,
                days=days
            )
            
            # Return the data
            response = jsonify(token_data)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        logger.error(f"Error in token movements API: {str(e)}")
        response = jsonify({
            'error': 'Server error',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500 