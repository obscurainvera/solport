from flask import Blueprint, jsonify, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from actions.WalletsInvestedAction import WalletsInvestedAction
from scheduler.WalletsInvestedScheduler import WalletsInvestedScheduler
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from decimal import Decimal
from database.operations.schema import WalletInvestedStatusEnum
import json

logger = get_logger(__name__)

# Create a custom JSON encoder to handle Decimal objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

# Create a Blueprint for token analysis endpoints
wallets_invested_bp = Blueprint('wallets_invested', __name__)

# Configure the blueprint to use the custom JSON encoder
@wallets_invested_bp.record
def record_params(setup_state):
    app = setup_state.app
    app.json_encoder = CustomJSONEncoder

@wallets_invested_bp.route('/api/walletsinvested/persist/token/<token_id>', methods=['POST', 'OPTIONS'])
def persistAllWalletsInvestedInASpecificPortSummarytoken(token_id):
    """API endpoint to trigger wallets invested analysis"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        if not token_id:
            response = jsonify({
                'status': 'error',
                'message': 'Token ID is required'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
    
        db = SQLitePortfolioDB()
        walletInvestedAction = WalletsInvestedAction(db)

        # 1. Check if token exists in portsummary
        tokenInfo = db.portfolio.getTokenDataFromPortSummary(token_id)
        if not tokenInfo:
            response = jsonify({
                'status': 'error',
                'message': f'Token {token_id} not found in portfolio summary'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404

        # 2. Get valid cookie for token analysis
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('walletsinvested', {})
            if isValidCookie(cookie, 'walletsinvested')
        ]

        if not validCookies:
            response = jsonify({
                'status': 'error',
                'message': 'No valid cookies available for wallets invested analysis'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # 3. Execute token analysis
        logger.info(f"Starting wallets invested analysis for {token_id}")
        
        # Get token age to report which API will be used
        token_age = Decimal(str(tokenInfo['tokenage']))
        using_new_api = token_age <= 1
        
        result = walletInvestedAction.fetchAndPersistWalletsInvestedInASpecificToken(
            cookie=validCookies[0],
            tokenId=token_id,
            portsummaryId=tokenInfo['portsummaryid'],
            tokenAge=token_age
        )

        if result:
            logger.info(f"Wallets invested analysis completed for {token_id}")
            response = jsonify({
                'status': 'success',
                'message': f'Wallets invested analysis completed for {token_id}',
                'data': {
                    'token_id': token_id,
                    'portsummary_id': tokenInfo['portsummaryid'],
                    'analysis_count': len(result),
                    'token_age': float(token_age),
                    'used_alternative_api': using_new_api
                }
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        logger.error(f"Failed to get analysis data for token {token_id}")
        response = jsonify({
            'status': 'error',
            'message': f'Failed to get analysis data for token {token_id}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

    except Exception as e:
        logger.error(f"Error in wallets invested analysis: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@wallets_invested_bp.route('/api/walletsinvested/persist/all', methods=['POST', 'OPTIONS'])
def persistAllSMWalletsInvestedInAnyPortSummaryToken():
    """API endpoint to trigger wallets invested analysis for all tokens"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Execute analysis for all tokens
        logger.info("Starting wallets invested analysis for all tokens")
        db = SQLitePortfolioDB()
        scheduler = WalletsInvestedScheduler()
        scheduler.handleWalletsInvestedInPortSummaryTokens()
        
        response = jsonify({
            'status': 'success',
            'message': 'Wallets invested analysis initiated for all tokens'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        logger.error(f"Error in wallets invested analysis for all tokens: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@wallets_invested_bp.route('/api/walletsinvested/token/<token_id>', methods=['GET', 'OPTIONS'])
def getWalletsInvestedInToken(token_id):
    """Get all wallets invested in a specific token with their investment details"""
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        with SQLitePortfolioDB() as db:
            # Get all wallets invested in this token
            # We use a very small minimum balance to get all wallets
            wallets = db.walletsInvested.getWalletsWithHighSMTokenHoldings(
                minBalance=Decimal('0.000'), 
                tokenId=token_id
            )
            
            if not wallets:
                logger.warning(f"No wallets found for token {token_id}")
                response = jsonify({
                    'wallets': [],
                    'token_id': token_id,
                    'count': 0
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            
            # Get detailed information for each wallet
            detailed_wallets = []
            wallet_addresses_needing_pnl = []
            wallet_address_to_index_map = {}
            
            for index, wallet in enumerate(wallets):
                wallet_id = wallet.get('walletinvestedid')
                wallet_details = db.walletsInvested.getWalletInvestedById(wallet_id)
                
                if wallet_details:
                    # Format the data to include only the required fields
                    formatted_wallet = {
                        'walletaddress': wallet_details.get('walletaddress'),
                        'walletname': wallet_details.get('walletname'),
                        'coinquantity': wallet_details.get('coinquantity'),
                        'smartholding': wallet_details.get('smartholding'),
                        'totalinvestedamount': wallet_details.get('totalinvestedamount'),
                        'amounttakenout': wallet_details.get('amounttakenout'),
                        'totalcoins': wallet_details.get('totalcoins'),
                        'avgentry': wallet_details.get('avgentry'),
                        'tags': wallet_details.get('tags'),
                        'chainedgepnl': wallet_details.get('chainedgepnl'),
                        'status': wallet_details.get('status')
                    }
                    
                    # Check if chainedgepnl is null or 0
                    chainedgepnl = wallet_details.get('chainedgepnl')
                    if chainedgepnl is None or (isinstance(chainedgepnl, (int, float, Decimal)) and float(chainedgepnl) == 0):
                        wallet_address = wallet_details.get('walletaddress')
                        if wallet_address:
                            wallet_addresses_needing_pnl.append(wallet_address)
                            wallet_address_to_index_map[wallet_address] = len(detailed_wallets)
                    
                    detailed_wallets.append(formatted_wallet)
            
            # If we have wallets needing PNL data, fetch it in batch using SmartMoneyWalletsHandler
            if wallet_addresses_needing_pnl:
                pnl_data = db.smartMoneyWallets.getWalletsProfitAndLoss(wallet_addresses_needing_pnl)
                
                # Update the chainedgepnl with profitandloss where needed
                for wallet_address, profitandloss in pnl_data.items():
                    if wallet_address in wallet_address_to_index_map:
                        index = wallet_address_to_index_map[wallet_address]
                        detailed_wallets[index]['chainedgepnl'] = profitandloss
            
            # Sort by smartholding in descending order
            detailed_wallets.sort(key=lambda x: float(x.get('smartholding', 0) or 0), reverse=True)
            
            response = jsonify({
                'wallets': detailed_wallets,
                'token_id': token_id,
                'count': len(detailed_wallets)
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
            
    except Exception as e:
        logger.error(f"Error getting wallets for token {token_id}: {str(e)}")
        response = jsonify({
            'error': 'Failed to retrieve wallets',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500 