from flask import Blueprint, jsonify, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from actions.WalletsInvestedInvestmentDetailsAction import WalletsInvestedInvestmentDetailsAction
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from decimal import Decimal
from scheduler.WalletsInvestedInvestmentDetailsScheduler import WalletsInvestedInvestmentDetailsScheduler
import json

logger = get_logger(__name__)

# Create a custom JSON encoder to handle Decimal objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

wallets_invested_investement_details_bp = Blueprint('wallets_invested_investement_details', __name__)

# Configure the blueprint to use the custom JSON encoder
@wallets_invested_investement_details_bp.record
def record_params(setup_state):
    app = setup_state.app
    app.json_encoder = CustomJSONEncoder

@wallets_invested_investement_details_bp.route('/api/walletinvestement/investmentdetails/token/wallet', methods=['POST', 'OPTIONS'])
def updateWalletInvesmentDetailsOfASMWalletForASpecificToken():
    """API endpoint to trigger transaction analysis for specific wallet and token"""
    if request.method == 'OPTIONS':
        return handle_options_request()
        
    try:
        # Get parameters from request
        data = request.get_json()
        tokenAddress = data.get('token_address')
        walletAddress = data.get('wallet_address')

        # Validate required parameters
        if not tokenAddress or not walletAddress:
            return create_response('error', 'Missing required parameters: token_id and wallet_address', 400)

        db = SQLitePortfolioDB()
        
        # Get wallet invested ID using the handler method
        walletInvestedId = db.walletsInvested.getWalletInvestedId(tokenAddress, walletAddress)
        
        if not walletInvestedId:
            return create_response('error', 
                f'No wallet invested record found for token {tokenAddress} and wallet {walletAddress}', 404)
            
        # Get valid cookies for transaction analysis
        validCookie = get_valid_solscan_cookie()
        if not validCookie:
            return create_response('error', 'No valid cookies available for transaction analysis', 400)
            
        # Execute transaction analysis
        action = WalletsInvestedInvestmentDetailsAction(db)
        success = action.updateInvestmentData(
            cookie=validCookie,
            walletAddress=walletAddress,
            tokenId=tokenAddress,
            walletInvestedId=walletInvestedId
        )
        
        if success:
            return create_response('success', 
                f'Transaction analysis completed for wallet {walletAddress} and token {tokenAddress}',
                200, {'wallet_invested_id': walletInvestedId})
        else:
            return create_response('error', 
                f'Failed to complete transaction analysis for wallet {walletAddress} and token {tokenAddress}', 500)
            
    except Exception as e:
        logger.error(f"Error in wallet investment details analysis: {str(e)}")
        return create_response('error', f'Internal server error: {str(e)}', 500)

@wallets_invested_investement_details_bp.route('/api/walletinvestement/investmentdetails/token/all', methods=['POST', 'OPTIONS'])
def updateInvestmentDetailsOfAllSMWalletsInvestedInASpecificToken():
    """API endpoint to trigger transaction analysis for all wallets invested in a specific token"""
    if request.method == 'OPTIONS':
        return handle_options_request()
        
    try:
        # Get token ID from request
        data = request.get_json()
        if not data:
            return create_response('error', 'Missing request data', 400)
            
        tokenAddress = data.get('token_address')
        minHolding = Decimal(str(data.get('min_holding'))) if data.get('min_holding') else None
        
        if not tokenAddress:
            return create_response('error', 'Missing required parameter: token_id', 400)
            
        # Get valid cookies for transaction analysis
        validCookie = get_valid_solscan_cookie()
        if not validCookie:
            return create_response('error', 'No valid cookies available for transaction analysis', 400)
            
        # Execute transaction analysis for all wallets invested in the token
        scheduler = WalletsInvestedInvestmentDetailsScheduler()
        scheduler.handleInvestmentDetailsOfAllWalletsInvestedInAToken(tokenAddress, cookie=validCookie, minHolding=minHolding)
        
        return create_response('success', 
            f'Transaction analysis initiated for all wallets invested in token {tokenAddress}')
        
    except Exception as e:
        logger.error(f"Error in wallet investment details analysis for all wallets: {str(e)}")
        return create_response('error', f'Internal server error: {str(e)}', 500)

@wallets_invested_investement_details_bp.route('/api/walletinvestement/investmentdetails/all', methods=['POST', 'OPTIONS'])
def updateInvestmentDetailsOfAllSMWalletsAboveCertainHoldings():
    """
    API endpoint to trigger transaction analysis for all wallets above specified smart holding
    """
    if request.method == 'OPTIONS':
        return handle_options_request()
        
    try:
        # Get parameters from request
        data = request.get_json()
        if not data:
            # If no data provided, use default minimum holding
            minSmartHolding = None
        else:
            minSmartHolding = data.get('min_smart_holding')

        # Convert to Decimal if provided
        if minSmartHolding:
            try:
                minSmartHolding = Decimal(str(minSmartHolding))
            except Exception as e:
                return create_response('error', f'Invalid min_smart_holding value: {str(e)}', 400)
        
        # Use default threshold if none provided
        default_threshold = WalletsInvestedInvestmentDetailsAction.MIN_SMART_HOLDING
        actual_threshold = minSmartHolding if minSmartHolding is not None else default_threshold

        db = SQLitePortfolioDB()
        scheduler = WalletsInvestedInvestmentDetailsScheduler(db)
        
        # Execute analysis with provided threshold
        scheduler.analyzeSMWalletInvestment(minSmartHolding=actual_threshold)
        
        return create_response('success', 'Smart wallet analysis scheduled successfully', 200, {
            'data': {
                'min_smart_holding': float(actual_threshold)
            }
        })

    except Exception as e:
        logger.error(f"Smart wallet analysis API error: {str(e)}")
        return create_response('error', f'Internal server error: {str(e)}', 500)

def get_valid_solscan_cookie():
    """Helper function to get a valid Solscan cookie"""
    validCookies = [
        cookie for cookie in COOKIE_MAP.get('solscan', {})
        if isValidCookie(cookie, 'solscan')
    ]
    
    return validCookies[0] if validCookies else None

def handle_options_request():
    """Helper function to handle OPTIONS requests with CORS headers"""
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
    return response, 200

def create_response(status, message, status_code=200, additional_data=None):
    """Helper function to create consistent API responses with CORS headers"""
    response_data = {
        'status': status,
        'message': message
    }
    
    # Add any additional data to the response
    if additional_data:
        # Convert any Decimal values to float before JSON serialization
        for key, value in additional_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, Decimal):
                        additional_data[key][sub_key] = float(sub_value)
            elif isinstance(value, Decimal):
                additional_data[key] = float(value)
        
        response_data.update(additional_data)
        
    response = jsonify(response_data)
    response.headers.add('Access-Control-Allow-Origin', '*')
    
    return response, status_code 