from flask import Blueprint, jsonify, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from scheduler.PortfolioScheduler import PortfolioScheduler
from config.Security import COOKIE_MAP, isValidCookie
from config.PortfolioStatusEnum import PortfolioStatus
from logs.logger import get_logger
from actions.DexscrennerAction import DexScreenerAction
from actions.portfolio.PortfolioSummaryAction import PortfolioSummaryAction
from database.operations.schema import PortfolioSummary
from decimal import Decimal
from datetime import datetime

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
            'message': 'Portfolio summary updated successfully',
            'stats': {
                'categoriesProcessed': result.get('categoriesProcessed', 0),
                'totalTokensProcessed': result.get('totalTokensProcessed', 0),
                'uniqueTokensProcessed': result.get('uniqueTokensProcessed', 0),
                'tokensInserted': result.get('tokensInserted', 0),
                'tokensUpdated': result.get('tokensUpdated', 0),
                'tokensReactivated': result.get('tokensReactivated', 0),
                'tokensMarkedInactive': result.get('tokensMarkedInactive', 0)
            }
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

@portfolio_bp.route('/api/portsummary/status', methods=['GET'])
def getPortfolioStatusTypes():
    """API endpoint to get all portfolio status types"""
    try:
        # Convert enum values to a list of dictionaries
        statuses = [
            {
                'code': status.statuscode,
                'name': status.statusname,
                'enum_name': status.name
            }
            for status in PortfolioStatus
        ]
        
        response = jsonify({
            'success': True,
            'data': statuses
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Error getting portfolio statuses: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@portfolio_bp.route('/api/portsummary/manual-persist', methods=['POST', 'OPTIONS'])
def handleManualTokenPersist():
    """API endpoint to manually persist a token in portfolio summary"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
    
    try:
        # Get token ID from request
        data = request.get_json()
        if not data or 'tokenId' not in data:
            return jsonify({
                'success': False,
                'message': 'Token ID is required'
            }), 400
        
        tokenId = data['tokenId']
        logger.info(f"Manual token persistence requested for token ID: {tokenId}")
        
        # Initialize database and actions
        db = SQLitePortfolioDB()
        dexScreener = DexScreenerAction()
        portfolioAction = PortfolioSummaryAction(db)
        
        # Get token details from DexScreener
        tokenPrice = dexScreener.getTokenPrice(tokenId)
        if not tokenPrice:
            return jsonify({
                'success': False,
                'message': f'Token not found on DexScreener: {tokenId}'
            }), 404
        
        # Create PortfolioSummary object
        currentTime = datetime.now()
        portfolioItem = PortfolioSummary(
            chainname="sol",
            tokenid=tokenId,
            name=tokenPrice.name,
            tokenage=tokenPrice.tokenAge,  # Use the tokenAge from DexScreener
            mcap=Decimal(str(tokenPrice.marketCap)),
            currentprice=Decimal(str(tokenPrice.price)),
            avgprice=Decimal('0'),  # Set to 0 as requested
            smartbalance=Decimal('0'),  # Set to 0 as requested
            walletsinvesting1000=0,  # Set to 0 as requested
            walletsinvesting5000=0,  # Set to 0 as requested
            walletsinvesting10000=0,  # Set to 0 as requested
            qtychange1d=Decimal('0'),  # Set to 0 as requested
            qtychange7d=Decimal('0'),  # Set to 0 as requested
            qtychange30d=Decimal('0'),  # Set to 0 as requested
            status=PortfolioStatus.ACTIVE.statuscode,
            firstseen=currentTime,
            lastseen=currentTime,
            createdat=currentTime,
            updatedat=currentTime
        )
        
        # Persist the token
        result = portfolioAction.persistPortfolioSummaryData([portfolioItem], ["all"])
        
        response = jsonify({
            'success': True,
            'message': 'Token persisted successfully',
            'data': {
                'tokenId': tokenId,
                'name': tokenPrice.name,
                'price': float(tokenPrice.price),
                'marketCap': float(tokenPrice.marketCap),
                'fdv': float(tokenPrice.fdv),
                'tokenAge': tokenPrice.tokenAge,
                'stats': result
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    except Exception as e:
        logger.error(f"Manual token persistence error: {str(e)}")
        response = jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

