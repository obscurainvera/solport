from flask import Blueprint, jsonify, request
from actions.TopTradersAction import TopTradersAction
from database.operations.sqlite_handler import SQLitePortfolioDB
from logs.logger import get_logger
import time
import os

logger = get_logger(__name__)

top_traders_bp = Blueprint('top_traders', __name__)

@top_traders_bp.route('/api/top-traders/process', methods=['POST', 'OPTIONS'])
def getAllLatestTopTraders():
    """
    Trigger top traders data processing manually
    
    Request Body (optional):
        {
            "cookie": "your_auth_cookie_here"  # Optional, will use default if not provided
        }
        
    Returns:
        JSON response with execution status and statistics
    """
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Accept')
        return response, 200
        
    start_time = time.time()
    logger.info("Manual top traders processing triggered")
    
    try:
        db = SQLitePortfolioDB()
        action = TopTradersAction(db)
        
        # Process top traders data
        success = action.getAllLatestTopTraders()
        
        execution_time = time.time() - start_time
        
        if success:
            logger.info(f"Top traders processing completed in {execution_time:.2f} seconds")
            response = jsonify({
                "status": "success",
                "message": "Top traders data processed successfully",
                "execution_time": f"{execution_time:.2f}s"
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        
        logger.error("Top traders processing failed")
        response = jsonify({
            "status": "error",
            "message": "Failed to process top traders data",
            "execution_time": f"{execution_time:.2f}s"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
        
    except Exception as e:
        logger.error(f"Error in processTopTraders: {str(e)}", exc_info=True)
        response = jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "execution_time": f"{time.time() - start_time:.2f}s"
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
