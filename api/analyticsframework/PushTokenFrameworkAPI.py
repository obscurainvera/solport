from flask import Blueprint, jsonify, request
from framework.analyticsframework.api.PushTokenFrameworkAPI import PushTokenAPI
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from framework.analyticsframework.enums.PushSourceEnum import PushSource
from framework.analyticsframework.models.BaseModels import BaseTokenData
from framework.analyticsframework.models.SourceModels import (
    PortSummaryTokenData, AttentionTokenData, SmartMoneyTokenData,
    VolumeTokenData, PumpFunTokenData
)
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from database.portsummary.PortfolioHandler import PortfolioHandler
from database.operations.sqlite_handler import SQLitePortfolioDB
from logs.logger import get_logger
from typing import Dict, Optional, List, Tuple
from decimal import Decimal

logger = get_logger(__name__)

# Create Blueprint for token analysis endpoints
push_token_bp = Blueprint('push_token', __name__)

def getSourceTokenDataHandler(sourceType: str, tokenId: str) -> Optional[BaseTokenData]:
    """
    Get token data from appropriate source
    
    Args:
        sourceType: Type of data source (PORTSUMMARY, ATTENTION, VOLUME, PUMPFUN, SMARTMONEY)
        tokenId: Token identifier
        
    Returns:
        Optional[BaseTokenData]: Mapped token data or None if not found
    """
    try:
        db = SQLitePortfolioDB()
        
        if sourceType == SourceType.PORTSUMMARY.value:
            portfolioHandler = PortfolioHandler(db)
            tokenData = portfolioHandler.getTokenDataForAnalysis(tokenId)
            if tokenData:
                return PushTokenAPI.mapPortfolioTokenData(tokenData)
                
        elif sourceType == SourceType.ATTENTION.value:
            attentionHandler = db.attention
            tokenData = attentionHandler.getTokenDataForAnalysis(tokenId)
            if tokenData:
                return PushTokenAPI.mapAttentionTokenData(tokenData)
                
        elif sourceType == SourceType.VOLUME.value:
            volumeHandler = db.volume
            tokenData = volumeHandler.getTokenState(tokenId)
            if tokenData:
                return PushTokenAPI.mapVolumeTokenData(tokenData)
                
        elif sourceType == SourceType.PUMPFUN.value:
            pumpfunHandler = db.pumpfun
            tokenData = pumpfunHandler.getTokenState(tokenId)
            if tokenData:
                return PushTokenAPI.mapPumpFunTokenData(tokenData)
                
        elif sourceType == SourceType.SMARTMONEY.value:
            # For smart money, we need to handle it differently as it's wallet-based
            # We'll get the top tokens for high PNL wallets
            smWalletHandler = db.smWalletTopPNLToken
            tokenData = smWalletHandler.getSMWalletTopPNLToken(None, tokenId)
            if tokenData:
                return PushTokenAPI.mapSmartMoneyTokenData(tokenData)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting token data: {str(e)}", exc_info=True)
        return None

@push_token_bp.route('/api/analyticsframework/pushtoken', methods=['POST'])
def pushToken():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Validate required fields
        tokenId = data.get('token_id')
        sourceType = data.get('source_type')
        
        if not tokenId or not sourceType:
            return jsonify({
                'status': 'error',
                'message': 'Missing required fields: token_id and source_type'
            }), 400

        if not SourceType.isValidSource(sourceType):
            return jsonify({
                'status': 'error',
                'message': f'Invalid source type: {sourceType}'
            }), 400

        # Get token data from source
        tokenData = getSourceTokenDataHandler(sourceType, tokenId)
        if not tokenData:
            return jsonify({
                'status': 'error',
                'message': f'Token {tokenId} not found in {sourceType} source'
            }), 404

        # Initialize analytics framework with database connection
        db = SQLitePortfolioDB()
        analyticsHandler = AnalyticsHandler(db)
        pushTokenApiInstance = PushTokenAPI(analyticsHandler)

        # Analyze token with source type, setting push source as API
        success = pushTokenApiInstance.pushToken(tokenData, sourceType, PushSource.API)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Token pushed to framework successfully',
                'data': {'token_id': tokenId, 'source': sourceType}
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to push token to framework'
            }), 500

    except Exception as e:
        logger.error(f"Token analysis API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500

@push_token_bp.route('/api/analyticsframework/pushallsourcetokens', methods=['POST'])
def pushAllSourceTokens():
    """
    API endpoint to push all tokens from a specific source type to the analytics framework
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        # Validate required field
        sourceType = data.get('source_type')
        
        if not sourceType:
            return jsonify({
                'status': 'error',
                'message': 'Missing required field: source_type'
            }), 400

        if not SourceType.isValidSource(sourceType):
            return jsonify({
                'status': 'error',
                'message': f'Invalid source type: {sourceType}'
            }), 400
            
        # Initialize database and analytics handler
        db = SQLitePortfolioDB()
        analyticsHandler = AnalyticsHandler(db)
        pushTokenApiInstance = PushTokenAPI(analyticsHandler)
        
        # Push all tokens for the specified source
        success, stats = pushTokenApiInstance.pushAllTokens(sourceType)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': f'Successfully pushed tokens from {sourceType} source to analytics framework',
                'data': stats
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Failed to push tokens from {sourceType} source',
                'data': stats
            }), 500

    except Exception as e:
        logger.error(f"Push all tokens API error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}'
        }), 500 