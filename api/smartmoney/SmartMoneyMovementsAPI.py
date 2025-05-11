from flask import jsonify, Blueprint, request, make_response
from database.operations.sqlite_handler import SQLitePortfolioDB
from actions.SmartMoneyMovementsAction import SmartMoneyMovementsAction
from logs.logger import get_logger
from typing import List, Dict, Optional
from datetime import datetime, timedelta

logger = get_logger(__name__)

smart_money_movements_bp = Blueprint('smart_money_movements', __name__)

# Add CORS headers to all responses
@smart_money_movements_bp.after_request
def after_request(response):
    """Add CORS headers to all responses"""
    # Clear any existing CORS headers to prevent duplicates
    response.headers.pop('Access-Control-Allow-Origin', None)
    response.headers.pop('Access-Control-Allow-Headers', None)
    response.headers.pop('Access-Control-Allow-Methods', None)
    
    # Add CORS headers
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept, Origin, Referer, User-Agent, sec-ch-ua, sec-ch-ua-mobile, sec-ch-ua-platform')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, POST, DELETE, OPTIONS')
    return response



def shouldProcessWallet(action: SmartMoneyMovementsAction, wallet_address: str) -> bool:
    """
    Check if wallet should be processed based on last fetch time
    
    Args:
        action: SmartMoneyMovementsAction instance
        wallet_address: Wallet address to check
        
    Returns:
        bool: True if should process, False if should skip
    """
    lastFetchedTime = action.smartMoneyMovementsHandler.getLastFetchedTime(wallet_address)
    if lastFetchedTime is None:
        return True
        
    currentTime = int(datetime.now().timestamp())
    timeDiff = currentTime - lastFetchedTime
    
    # Skip if less than 24 hours
    return timeDiff >= 24 * 3600

@smart_money_movements_bp.route('/api/smartmoneymovements/process/wallet', methods=['POST', 'OPTIONS'])
def process_wallet_movements():
    """Process smart money movements for a specific wallet"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        return make_response(jsonify({}), 200)

    try:
        data = request.get_json()
        logger.info(f"Received request data: {data}")
        
        if not data or 'wallet_address' not in data:
            logger.error("Missing wallet_address in request data")
            return jsonify({'error': 'Wallet address is required'}), 400

        walletAddress = data['wallet_address']
        logger.info(f"Processing wallet: {walletAddress}")
        
        db = SQLitePortfolioDB('portfolio.db')
        action = SmartMoneyMovementsAction(db)
        
        # Check if we should process this wallet
        if not shouldProcessWallet(action, walletAddress):
            response = jsonify({
                'success': True,
                'message': f'Skipped processing for wallet {walletAddress} - last fetch was less than 24 hours ago'
            })
        
        success = action.processWalletMovements(walletAddress)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Successfully processed movements for wallet {walletAddress}'
            })
        
        return jsonify({
            'success': False,
            'error': f'Failed to process movements for wallet {walletAddress}'
        }), 500

    except Exception as e:
        logger.error(f"Error processing wallet movements: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@smart_money_movements_bp.route('/api/smartmoneymovements/process/token', methods=['POST', 'OPTIONS'])
def process_token_movements():
    """Process smart money movements for all active wallets of a token"""
    if request.method == 'OPTIONS':
        # Handle preflight request
        return make_response(jsonify({}), 200)

    try:
        data = request.get_json()
        logger.info(f"Received token request data: {data}")
        
        if not data or 'token_address' not in data:
            logger.error("Missing token_address in request data")
            return jsonify({'error': 'Token address is required'}), 400

        tokenAddress = data['token_address']
        logger.info(f"Processing token: {tokenAddress}")
        
        db = SQLitePortfolioDB('portfolio.db')
        action = SmartMoneyMovementsAction(db)
        
        # Get all active wallets for the token
        activeWalletsAddresses = db.walletsInvested.getActiveWalletsByTokenId(tokenAddress)
        if not activeWalletsAddresses:
            return jsonify({
                'success': True,
                'message': f'No active wallets found for token {tokenAddress}'
            })
            
        # Process movements for each wallet
        results: List[Dict[str, str]] = []
        skipped_count = 0
        
        for walletAddress in activeWalletsAddresses:
            
            # Check if we should process this wallet
            if not shouldProcessWallet(action, walletAddress):
                results.append({
                    'wallet_address': walletAddress,
                    'status': 'skipped',
                    'message': 'Last fetch was less than 24 hours ago'
                })
                skipped_count += 1
                continue
                
            try:
                success = action.processWalletMovements(walletAddress)
                results.append({
                    'wallet_address': walletAddress,
                    'status': 'success' if success else 'failed'
                })
            except Exception as e:
                logger.error(f"Failed to process wallet {walletAddress}: {str(e)}")
                results.append({
                    'wallet_address': walletAddress,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Count results by status
        successCount = sum(1 for r in results if r['status'] == 'success')
        failureCount = sum(1 for r in results if r['status'] == 'failed')
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(results)} wallets',
            'details': {
                'total_wallets': len(results),
                'successful': successCount,
                'failed': failureCount,
                'skipped': skipped_count,
                'results': results
            }
        })

    except Exception as e:
        logger.error(f"Error processing token movements: {str(e)}")
        return jsonify({'error': str(e)}), 500 