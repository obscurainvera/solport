from flask import jsonify, Blueprint, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from actions.portfolio.PortfolioTaggerAction import PortfolioTaggerAction
from logs.logger import get_logger

logger = get_logger(__name__)

portfolio_tagger_bp = Blueprint('portfolio_tagger', __name__)

@portfolio_tagger_bp.route('/api/portfoliotagger/persist', methods=['POST', 'OPTIONS'])
def tagPortfolioTokens():
    """API endpoint to initiate portfolio token tagging process"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        db = SQLitePortfolioDB('portfolio.db')
        tagger = PortfolioTaggerAction(db)
        
        success = tagger.addTagsToActivePortSummaryTokens()
        
        if success:
            response = jsonify({
                'success': True,
                'message': 'Successfully tagged portfolio tokens'
            })
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
            return response
            
        response = jsonify({'error': 'Failed to tag portfolio tokens'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response, 500

    except Exception as e:
        logger.error(f"API Error in portfolio tagging: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response, 500

@portfolio_tagger_bp.route('/api/portfoliotagger/getalltags', methods=['GET', 'OPTIONS'])
def getAvailableTags():
    """API endpoint to get list of all available portfolio tags"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        from actions.portfolio.PortfolioTagEnum import PortfolioTokenTag
        
        tags = PortfolioTokenTag.getAllTags()
        response = jsonify({
            'success': True,
            'tags': tags
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response

    except Exception as e:
        logger.error(f"API Error getting portfolio tags: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response, 500

@portfolio_tagger_bp.route('/api/portfoliotagger/token/persist', methods=['POST', 'OPTIONS'])
def evaluateTokenTags():
    """API endpoint to evaluate and update tags for a specific token"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get token ID from request body
        requestData = request.get_json()
        if not requestData or 'token_id' not in requestData:
            response = jsonify({'error': 'token_id is required'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
            return response, 400
            
        tokenId = requestData['token_id']
        
        # Initialize database and tagger
        db = SQLitePortfolioDB('portfolio.db')
        tagger = PortfolioTaggerAction(db)
        
        # Get token data - wrap token_id in a list since getTokenData expects List[str]
        tokens = db.portfolio.getTokenData([tokenId])
        if not tokens:
            response = jsonify({'error': f'Token {tokenId} not found'})
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
            return response, 404
            
        # Use first token since we only expect one
        token = tokens[0]
        
        # Evaluate and update tags
        result = tagger.evaluateAndUpdateTokenTags(token)
        
        response = jsonify({
            'success': True,
            'data': result
        })
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response

    except Exception as e:
        logger.error(f"API Error in token tag evaluation: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        return response, 500 