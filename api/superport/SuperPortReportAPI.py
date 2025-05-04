from flask import Blueprint, jsonify, request
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.superport.SuperPortReportHandler import SuperPortReportHandler
from logs.logger import get_logger
from datetime import datetime
import time
from typing import Dict, Any, Optional, List

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
        # Parse all query parameters
        params = _parse_query_parameters(request)
        
        # Log the query parameters
        logger.info(f"Fetching SuperPort report with params: {params}")
        
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
            
            # Get the report data with all filters applied directly in the query
            combined_data = handler.getSuperPortReport(**params)
            
            # Calculate performance metrics
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Format the data for the UI
            formatted_data = _format_response_data(combined_data)
            
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


def _parse_query_parameters(request) -> Dict[str, Any]:
    """
    Parse and validate all query parameters from the request.
    
    Args:
        request: Flask request object
        
    Returns:
        Dictionary of validated parameters for the handler
    """
    # Token identification filters
    params = {
        'tokenId': request.args.get('token_id', ''),
        'name': request.args.get('name', ''),
        'chainName': request.args.get('chain_name', ''),
        
        # Market filters
        'minMarketCap': request.args.get('min_market_cap', type=float),
        'maxMarketCap': request.args.get('max_market_cap', type=float),
        
        # Token age filters
        'minTokenAge': request.args.get('minTokenAge', type=float),
        'maxTokenAge': request.args.get('maxTokenAge', type=float),
        
        # Attention filters
        'minAttentionCount': request.args.get('min_attention_count', type=int),
        
        # Sort options
        'sortBy': request.args.get('sortBy', 'smartbalance'),
        'sortOrder': request.args.get('sortOrder', 'desc'),
        
        # Wallet breakdown filters
        'walletCategory': request.args.get('walletCategory', ''),
        'walletType': request.args.get('walletType', ''),
        'minWalletCount': request.args.get('minWalletCount', type=int, default=0),
        'minAmountInvested': request.args.get('minAmountInvested', type=float, default=0)
    }
    
    # Remove None values
    return {k: v for k, v in params.items() if v is not None}


def _format_response_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Format and enhance the data for the UI response with the new wallet data structure.
    
    Args:
        data: List of token data dictionaries
        
    Returns:
        Formatted data ready for JSON response with the new wallet_data structure
    """
    formatted_data = []
    
    for item in data:
        # Create the new wallet_data structure
        wallet_data = {
            # Category 1: 0-300K
            '0-300K': _format_category_data(item, 1),
            
            # Category 2: 300K-1M
            '300K-1M': _format_category_data(item, 2),
            
            # Category 3: >1M
            '>1M': _format_category_data(item, 3)
        }
        
        # Create a new item with the basic token info and the wallet_data
        formatted_item = {
            'attention_count': item.get('attention_count', 0),
            'attention_status': item.get('attention_status', 'UNKNOWN'),
            'avgprice': item.get('avgprice', 0),
            'chainname': item.get('chainname', ''),
            'mcap': item.get('mcap', 0),
            'name': item.get('name', ''),
            'tokenid': item.get('tokenid', ''),
            'token_age': item.get('token_age', 0),
            'wallet_data': wallet_data
        }
        
        # Add any other fields that might be needed
        for key, value in item.items():
            if key not in formatted_item and not key.startswith('pnl_category'):
                formatted_item[key] = value
        
        formatted_data.append(formatted_item)
    
    return formatted_data


def _format_category_data(item: Dict[str, Any], category: int) -> Dict[str, Any]:
    """
    Format data for a specific PNL category (1, 2, or 3).
    
    Args:
        item: Token data dictionary
        category: PNL category number (1, 2, or 3)
        
    Returns:
        Formatted category data dictionary
    """
    # Get the total counts and amounts for this category
    total_wallets = item.get(f'pnl_category_{category}_count', 0) or 0
    
    # Calculate total invested amount across all subcategories
    no_withdrawal_total = item.get(f'pnl_category_{category}_no_withdrawal_total', 0) or 0
    partial_withdrawal_total = item.get(f'pnl_category_{category}_partial_withdrawal_total', 0) or 0
    significant_withdrawal_total = item.get(f'pnl_category_{category}_significant_withdrawal_total', 0) or 0
    
    total_invested_amount = round(float(no_withdrawal_total + partial_withdrawal_total + significant_withdrawal_total), 2)
    
    # Get the amount taken out for each subcategory
    no_withdrawal_taken_out = item.get(f'pnl_category_{category}_no_withdrawal_taken_out', 0) or 0
    partial_withdrawal_taken_out = item.get(f'pnl_category_{category}_partial_withdrawal_taken_out', 0) or 0
    significant_withdrawal_taken_out = item.get(f'pnl_category_{category}_significant_withdrawal_taken_out', 0) or 0
    
    # Calculate total amount taken out
    total_amount_taken_out = round(float(no_withdrawal_taken_out + partial_withdrawal_taken_out + significant_withdrawal_taken_out), 2)
    
    # Create the category data structure
    category_data = {
        'No Selling': {
            'total_number_of_wallets': item.get(f'pnl_category_{category}_no_withdrawal_count', 0) or 0,
            'total_invested_amount': round(float(no_withdrawal_total), 2),
            'total_amount_taken_out': round(float(no_withdrawal_taken_out), 2)  # Should be 0 by definition
        },
        '<30%': {
            'total_number_of_wallets': item.get(f'pnl_category_{category}_partial_withdrawal_count', 0) or 0,
            'total_invested_amount': round(float(partial_withdrawal_total), 2),
            'total_amount_taken_out': round(float(partial_withdrawal_taken_out), 2)
        },
        '>30%': {
            'total_number_of_wallets': item.get(f'pnl_category_{category}_significant_withdrawal_count', 0) or 0,
            'total_invested_amount': round(float(significant_withdrawal_total), 2),
            'total_amount_taken_out': round(float(significant_withdrawal_taken_out), 2)
        }
    }
    
    return {
        'total_number_of_wallets': total_wallets,
        'total_invested_amount': total_invested_amount,
        'total_amount_taken_out': total_amount_taken_out,
        'category_data': category_data
    }