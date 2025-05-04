from flask import Blueprint, jsonify, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.superport.SuperPortReportHandler import SuperPortReportHandler
from logs.logger import get_logger
from datetime import datetime
import time

logger = get_logger(__name__)

superport_report_bp = Blueprint('superport_report', __name__)

@superport_report_bp.route('/api/reports/superportreport', methods=['GET', 'OPTIONS'])
def getSuperPortReport():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')  # Allow any origin for development
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    try:
        # Get query parameters with defaults
        tokenId = request.args.get('token_id', '')
        name = request.args.get('name', '')
        chainName = request.args.get('chain_name', '')
        
        # Wallet breakdown filters
        walletCategory = request.args.get('walletCategory', '')
        walletType = request.args.get('walletType', '')
        minWalletCount = request.args.get('minWalletCount', type=int, default=0)
        minAmountInvested = request.args.get('minAmountInvested', type=float, default=0)
        
        # Legacy filters
        minMarketCap = request.args.get('min_market_cap', type=float)
        maxMarketCap = request.args.get('max_market_cap', type=float)
        minAttentionCount = request.args.get('min_attention_count', type=int)
        
        # Sort options
        sortBy = request.args.get('sortBy', 'smartbalance')
        sortOrder = request.args.get('sortOrder', 'desc')
        
        logger.info(f"Fetching SuperPort report with params: token_id={tokenId}, name={name}, chain_name={chainName}")
        logger.info(f"Wallet filters: category={walletCategory}, type={walletType}, minCount={minWalletCount}, minAmount={minAmountInvested}")
        
        # Use the handler to get the data
        with SQLitePortfolioDB() as db:
            handler = SuperPortReportHandler(db)
            
            # Check if handler is None
            if handler is None:
                logger.error("Handler 'superport_report' not found")
                response = jsonify({
                    'error': 'Configuration error',
                    'message': "Handler 'superport_report' not found"
                })
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 500
                
            # Start timing the operation
            start_time = time.time()
            
            # Get the initial report data
            combined_data = handler.getSuperPortReport(
                tokenId=tokenId,
                name=name,
                chainName=chainName,
                minMarketCap=minMarketCap,
                maxMarketCap=maxMarketCap,
                minAttentionCount=minAttentionCount,
                sortBy=sortBy,
                sortOrder=sortOrder
            )
            
            # Apply wallet breakdown filters if any are set
            if walletCategory or walletType or minWalletCount > 0 or minAmountInvested > 0:
                combined_data = handler.filterTokensByWalletBreakdown(
                    combined_data,
                    category=walletCategory,
                    type_filter=walletType,
                    min_wallets=minWalletCount,
                    min_amount=minAmountInvested
                )
            
            # Calculate performance metrics
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Format and enhance the data for the UI
            formatted_data = []
            for item in combined_data:
                # Calculate totals for each PNL category
                for category in range(1, 4):
                    # Total wallets in category
                    category_count = item.get(f'pnl_category_{category}_count', 0)
                    
                    # Total investment amount across all subcategories
                    category_total = (
                        item.get(f'pnl_category_{category}_no_withdrawal_total', 0) +
                        item.get(f'pnl_category_{category}_partial_withdrawal_total', 0) +
                        item.get(f'pnl_category_{category}_significant_withdrawal_total', 0)
                    )
                    
                    # Add the totals to the item
                    item[f'pnl_category_{category}_total_wallets'] = category_count
                    item[f'pnl_category_{category}_total_invested'] = category_total
                
                # Format decimal values for JSON serialization
                for key, value in item.items():
                    if isinstance(value, (float, int)) and key.endswith('_total'):
                        item[key] = round(float(value), 2)
                
                formatted_data.append(item)
            
            logger.info(f"SuperPort report generated with {len(formatted_data)} records in {execution_time:.2f} seconds")
            
            # Add metadata to the response
            response_data = {
                'data': formatted_data,
                'metadata': {
                    'count': len(formatted_data),
                    'execution_time_seconds': round(execution_time, 2),
                    'generated_at': datetime.now().isoformat()
                }
            }

        # Create response with proper CORS headers
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')  # Allow any origin for development
        return response

    except Exception as e:
        logger.error(f"Error in SuperPort report API: {str(e)}", exc_info=True)
        response = jsonify({
            'error': 'Internal server error',
            'message': str(e)
        })
        response.headers.add('Access-Control-Allow-Origin', '*')  # Allow any origin for development
        return response, 500 