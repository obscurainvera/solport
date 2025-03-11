from flask import jsonify, Blueprint, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from actions.SmartMoneyWalletsAction import SmartMoneyWalletsAction
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from database.smartmoneywallets.WalletPNLStatusEnum import SmartWalletPnlStatus

logger = get_logger(__name__)

smart_money_wallets_bp = Blueprint('smart_money_wallets', __name__)

@smart_money_wallets_bp.route('/api/smartmoneywallets/persist', methods=['POST', 'OPTIONS'])
def persistAllSmartMoneyWallets():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('smartmoneywallets', {})
            if isValidCookie(cookie, 'smartmoneywallets')
        ]

        if not validCookies:
            response = jsonify({'error': 'No valid cookies available'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        db = SQLitePortfolioDB('portfolio.db')
        action = SmartMoneyWalletsAction(db)
        
        success = action.getAllSmartMoneyWallets(cookie=validCookies[0])
        
        if success:
            response = jsonify({
                'success': True,
                'message': 'Successfully persisted all smart money wallets'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
        response = jsonify({'error': 'Failed to persist smart money wallets'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@smart_money_wallets_bp.route('/api/smartmoneywallets/list', methods=['GET', 'OPTIONS'])
def getWalletBehaviours():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        db = SQLitePortfolioDB('portfolio.db')
        wallets = db.smartMoneyWallets.getAllSmartMoneyWallets()
        
        response = jsonify({
            'wallets': [{
                'address': w['walletaddress'],
                'pnl': float(w['profitandloss']),
                'trades': w['tradecount'],
                'lastUpdate': w['lastupdatetime'],
                'status': w['status'],
                'statusDescription': SmartWalletPnlStatus.getDescription(w['status'])
            } for w in wallets]
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        logger.error(f"API Error: {str(e)}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500 