from flask import Blueprint, jsonify, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from scheduler.PortfolioScheduler import PortfolioScheduler
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger

logger = get_logger(__name__)

# Create a Blueprint for portfolio endpoints
portfolio_bp = Blueprint('portfolio', __name__)

@portfolio_bp.route('/api/portsummary/update', methods=['POST', 'OPTIONS'])
def handlePortSummaryUpdate():
    """API endpoint to manually trigger portfolio update"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        db = SQLitePortfolioDB()
        portfolioScheduler = PortfolioScheduler(db)

        # Execute portfolio analysis
        logger.info("Starting manual portfolio update")
        result = portfolioScheduler.handlePortfolioSummaryUpdate()

        response = jsonify({
            'success': True,
            'message': 'Portfolio summary updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        logger.error(f"Manual portfolio update error: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

