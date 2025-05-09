from flask import Blueprint, jsonify, request
from framework.analyticsframework.api.CreateStrategyAPI import CreateStrategyAPI
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from database.operations.sqlite_handler import SQLitePortfolioDB
from framework.analyticsframework.models.StrategyModels import (
    StrategyConfig, StrategyEntryConditions, ChartConditions, InvestmentInstructions,
    ProfitTakingInstructions, RiskManagementInstructions
)
from logs.logger import get_logger 
from typing import Dict, Any
from decimal import Decimal, InvalidOperation

logger = get_logger(__name__)

# Create Blueprint for strategy endpoints
strategy_bp = Blueprint('strategy', __name__)

@strategy_bp.route('/api/strategy/create', methods=['POST'])
def addStrategy():
    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        # Initialize database and handlers
        db = SQLitePortfolioDB('portfolio.db')
        analyticsHandler = AnalyticsHandler(db)
        strategyApi = CreateStrategyAPI(analyticsHandler)
        
        # Log incoming data for debugging
        logger.debug(f"Received strategy creation data: {data}")
        
        # Process superuser field - ensure it's a boolean
        if 'superuser' in data:
            data['superuser'] = bool(data['superuser'])
        
        strategyId = strategyApi.addStrategy(data)
        
        if not strategyId:
            logger.error("Failed to create strategy - no ID returned")
            return jsonify({
                'status': 'error',
                'message': 'Failed to create strategy'
            }), 500

        logger.info(f"Successfully created strategy with ID: {strategyId}")
        return jsonify({
            'status': 'success',
            'message': 'Strategy created successfully',
            'strategy_id': strategyId
        }), 201
            
    except ValueError as e:
        logger.warning(f"Validation error in strategy creation: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Unexpected error adding strategy: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@strategy_bp.route('/api/strategy/<int:strategy_id>', methods=['PUT'])
def updateStrategy(strategyId):
    """Update an existing strategy"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'status': 'error',
                'message': 'No data provided'
            }), 400

        analyticsHandler = AnalyticsHandler()
        strategyApi = CreateStrategyAPI(analyticsHandler)
        
        success = strategyApi.updateStrategy(strategyId, data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Strategy updated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to update strategy'
            }), 500
            
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"Error updating strategy: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500

@strategy_bp.route('/api/strategy/<int:strategy_id>/activate', methods=['POST'])
def activateStrategy(strategyId):
    """Activate a strategy"""
    try:
        analyticsHandler = AnalyticsHandler()
        strategyApi = CreateStrategyAPI(analyticsHandler)
        
        success = strategyApi.activateStrategy(strategyId)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Strategy activated successfully'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to activate strategy'
            }), 500
            
    except Exception as e:
        logger.error(f"Error activating strategy: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500