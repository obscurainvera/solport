from flask import jsonify, Blueprint, request
from scheduler.SMWalletTopPNLTokenScheduler import SMWalletTopPnlTokenScheduler
from actions.SMWalletTopPNLTokenAction import SMWalletTopPNLTokenAction
from database.operations.sqlite_handler import SQLitePortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger

logger = get_logger(__name__)

smwallet_top_pnl_token_bp = Blueprint('smwallet_top_pnl_token', __name__)

@smwallet_top_pnl_token_bp.route('/api/smwallettoppnltoken/persist', methods=['POST', 'OPTIONS'])
def persistAllSMWalletTopPNLTokens():
    """Persist all top PNL tokens for all the smart money wallets"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        scheduler = SMWalletTopPnlTokenScheduler()
        scheduler.persistAllTopPNLTokensForHighPNLSMWallets()
        
        response = jsonify({
            'success': True,
            'message': 'Successfully triggered top PNL token analysis for all eligible wallets'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@smwallet_top_pnl_token_bp.route('/api/smwallettoppnltoken/wallet/persist', methods=['POST', 'OPTIONS'])
def analyzeTopPNLTokensForASpecificWallet():
    """Persist all top PNL tokens for a specific smart money wallet"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        data = request.get_json()
        walletAddress = data.get('wallet_address')
        
        if not walletAddress:
            response = jsonify({'error': 'Wallet address is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Get valid cookies
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('smwallettoppnltoken', {})
            if isValidCookie(cookie, 'smwallettoppnltoken')
        ]

        if not validCookies:
            response = jsonify({'error': 'No valid cookies available'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Initialize action and execute
        db = SQLitePortfolioDB('portfolio.db')
        action = SMWalletTopPNLTokenAction(db)
        
        result = action.persistAllTopPNLTokensForASMWallet(
            cookie=validCookies[0],
            walletAddress=walletAddress,
            lookbackDays=180
        )
        
        if result:
            response = jsonify({
                'success': True,
                'message': f'Successfully analyzed top PNL tokens for wallet {walletAddress}',
                'tokens_analyzed': len(result)
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        response = jsonify({
            'success': False,
            'message': f'No tokens found or analysis failed for wallet {walletAddress}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404

    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500 