# api/smwallet_behaviour/smwallet_behaviour_api.py
from flask import Blueprint, jsonify
from actions.SMWalletBehaviourAction import SMWalletBehaviourAction
from logs.logger import get_logger
import time

logger = get_logger(__name__)

smwallet_behaviour_bp = Blueprint('smwallet_behaviour', __name__)

@smwallet_behaviour_bp.route('/api/smwallet-behaviour/analyze', methods=['POST'])
def analyzeSMWalletBehaviour():
    """Trigger SM wallet behaviour analysis manually"""
    startTime = time.time()
    logger.info("Manual SM wallet behaviour analysis triggered")
    
    try:
        action = SMWalletBehaviourAction()
        result = action.analyzeSMWalletBehaviour()
        executionTime = time.time() - startTime
        
        if result:
            logger.info(f"SM wallet behaviour analysis completed in {executionTime:.2f} seconds")
            return jsonify({
                "status": "success",
                "message": "SM wallet behaviour analysis completed successfully",
                "executionTime": f"{executionTime:.2f}s"
            })
        
        logger.error("SM wallet behaviour analysis failed - no data processed")
        return jsonify({
            "status": "error",
            "message": "No SM wallet behaviour data processed",
            "executionTime": f"{executionTime:.2f}s"
        }), 500
        
    except Exception as e:
        executionTime = time.time() - startTime
        errorMessage = f"SM wallet behaviour analysis failed: {str(e)}"
        logger.error(errorMessage)
        return jsonify({
            "status": "error",
            "message": errorMessage,
            "executionTime": f"{executionTime:.2f}s"
        }), 500