from typing import Optional, Dict, Any, List
from framework.analyticsframework.models.BaseModels import BaseTokenData, BaseStrategyConfig
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.models.SourceModels import (
    PortSummaryTokenData, AttentionTokenData, SmartMoneyTokenData,
    VolumeTokenData, PumpFunTokenData
)
from framework.analyticsframework.strategies.PortSummaryStrategy import PortSummaryStrategy
from framework.analyticsframework.strategies.AttentionStrategy import AttentionStrategy
from framework.analyticsframework.strategies.VolumeStrategy import VolumeStrategy
from framework.analyticsframework.strategies.PumpfunStrategy import PumpFunStrategy
from framework.analyticsframework.StrategyFramework import StrategyFramework
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from framework.analyticsframework.models.StrategyModels import StrategyConfig
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from logs.logger import get_logger

logger = get_logger(__name__)

class PushTokenAPI:
    """API for analyzing tokens through the analytics framework"""
    
    def __init__(self, analyticsHandler: AnalyticsHandler):
        self.analyticsHandler = analyticsHandler
        self.strategyFramework = StrategyFramework(analyticsHandler)
        
        # Initialize strategy handlers
        self.strategyHandlers = {
            SourceType.PORTSUMMARY.value: PortSummaryStrategy(analyticsHandler),
            SourceType.ATTENTION.value: AttentionStrategy(analyticsHandler),
            SourceType.VOLUME.value: VolumeStrategy(analyticsHandler),
            SourceType.PUMPFUN.value: PumpFunStrategy(analyticsHandler)
        }
    
    @staticmethod
    def mapPortfolioTokenData(tokenData: Dict) -> PortSummaryTokenData:
        """
        Map raw portfolio token data to PortSummaryTokenData model
        
        Args:
            tokenData: Raw token data from database
            
        Returns:
            PortSummaryTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            'tokenid': tokenData['tokenid'],
            'tokenname': tokenData['name'],
            'chainname': tokenData['chainname'],
            'price': tokenData['currentprice'],
            'marketcap': tokenData['mcap'],
            'holders': tokenData.get('walletsinvesting1000', 0),  # Using this as holders count
            
            # PortSummaryTokenData specific fields
            'tokenage': tokenData['tokenage'],
            'avgprice': tokenData['avgprice'],
            'smartbalance': tokenData['smartbalance'],
            'walletsinvesting1000': tokenData['walletsinvesting1000'],
            'walletsinvesting5000': tokenData['walletsinvesting5000'],
            'walletsinvesting10000': tokenData['walletsinvesting10000'],
            'qtychange1d': tokenData['qtychange1d'],
            'qtychange7d': tokenData['qtychange7d'],
            'qtychange30d': tokenData['qtychange30d'],
            'status': tokenData['status'],
            'portsummaryid': tokenData.get('portsummaryid'),
            'tags': tokenData.get('tags'),
            'markedinactive': tokenData.get('markedinactive')
        }
        return PortSummaryTokenData(**mappedData)
    
    def pushToken(self, tokenData: BaseTokenData, sourceType: str) -> bool:
        """
        Analyze a token through all applicable strategies
        
        Args:
            tokenData: Token data from source
            sourceType: Type of data source
            
        Returns:
            bool: Success status
        """
        try:
            # Get active strategies for token's source type
            allActiveStrategies: List[Dict] = self.analyticsHandler.getAllActiveStrategies(sourceType)
            
            if not allActiveStrategies:
                logger.info(f"No active strategies found for source {sourceType}")
                return False
            
            # Get the appropriate strategy handler
            strategyHandler = self.strategyHandlers.get(sourceType)
            if not strategyHandler:
                logger.error(f"No strategy handler found for source type: {sourceType}")
                return False
                
            success = False
            for strategy in allActiveStrategies:
                # Convert dictionary to StrategyConfig
                strategyConfig = StrategyConfig(**strategy)
                
                # Process token through strategy
                executionId = self.strategyFramework.handleStrategy(
                    strategy=strategyHandler,
                    tokenData=tokenData,
                    strategyConfig=strategyConfig
                )
                
                if executionId:
                    success = True
                    logger.info(
                        f"Successfully processed token {tokenData.tokenid} "
                        f"with strategy {strategyConfig.strategyid} "
                        f"(execution_id: {executionId})"
                    )
                    
            return success
            
        except Exception as e:
            logger.error(f"Error analyzing token: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def mapAttentionTokenData(tokenData: Dict) -> AttentionTokenData:
        """
        Map raw attention token data to AttentionTokenData model
        
        Args:
            tokenData: Raw token data from database
            
        Returns:
            AttentionTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            'tokenid': tokenData['tokenid'],
            'tokenname': tokenData.get('name', ''),
            'chainname': tokenData.get('chain', ''),
            'price': 0,  # Attention data doesn't have price
            'marketcap': 0,  # Attention data doesn't have marketcap
            'holders': 0,  # Attention data doesn't have holders
            
            # AttentionTokenData specific fields
            'attentionscore': tokenData['attentionscore'],
            'change1hbps': tokenData.get('change1hbps'),
            'change1dbps': tokenData.get('change1dbps'),
            'change7dbps': tokenData.get('change7dbps'),
            'change30dbps': tokenData.get('change30dbps'),
            'recordedat': tokenData['recordedat'],
            'datasource': tokenData['datasource']
        }
        return AttentionTokenData(**mappedData)

    @staticmethod
    def mapVolumeTokenData(tokenData: Dict) -> VolumeTokenData:
        """
        Map raw volume token data to VolumeTokenData model
        
        Args:
            tokenData: Raw token data from database
            
        Returns:
            VolumeTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            'tokenid': tokenData['tokenid'],
            'tokenname': tokenData.get('tokenname', tokenData.get('name', '')),
            'chainname': tokenData.get('chain', ''),
            'price': tokenData.get('price', 0),
            'marketcap': tokenData.get('marketcap', 0),
            'holders': 0,  # Volume data doesn't typically have holders
            
            # VolumeTokenData specific fields
            'name': tokenData.get('name', ''),  # Trading symbol
            'liquidity': tokenData.get('liquidity', 0),
            'volume24h': tokenData.get('volume24h', 0),
            'buysolqty': tokenData.get('buysolqty', 0),
            'occurrencecount': tokenData.get('occurrencecount', 0),
            'percentilerankpeats': tokenData.get('percentilerankpeats', 0),
            'percentileranksol': tokenData.get('percentileranksol', 0),
            'dexstatus': tokenData.get('dexstatus', False),
            'change1hpct': tokenData.get('change1hpct', 0),
            'tokendecimals': tokenData.get('tokendecimals'),
            'circulatingsupply': tokenData.get('circulatingsupply'),
            'tokenage': tokenData.get('tokenage'),
            'twitterlink': tokenData.get('twitterlink'),
            'telegramlink': tokenData.get('telegramlink'),
            'websitelink': tokenData.get('websitelink'),
            'firstseenat': tokenData.get('firstseenat'),
            'lastupdatedat': tokenData.get('lastupdatedat'),
            'createdat': tokenData.get('createdat'),
            'fdv': tokenData.get('fdv')
        }
        return VolumeTokenData(**mappedData)

    @staticmethod
    def mapPumpFunTokenData(tokenData: Dict) -> PumpFunTokenData:
        """
        Map raw pump fun token data to PumpFunTokenData model
        
        Args:
            tokenData: Raw token data from database
            
        Returns:
            PumpFunTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            'tokenid': tokenData['tokenid'],
            'tokenname': tokenData.get('tokenname', tokenData.get('name', '')),
            'chainname': tokenData.get('chain', ''),
            'price': tokenData.get('price', 0),
            'marketcap': tokenData.get('marketcap', 0),
            'holders': 0,  # Pump fun data doesn't typically have holders
            
            # PumpFunTokenData specific fields
            'name': tokenData.get('name', ''),  # Trading symbol
            'liquidity': tokenData.get('liquidity', 0),
            'volume24h': tokenData.get('volume24h', 0),
            'buysolqty': tokenData.get('buysolqty', 0),
            'occurrencecount': tokenData.get('occurrencecount', 0),
            'percentilerankpeats': tokenData.get('percentilerankpeats', 0),
            'percentileranksol': tokenData.get('percentileranksol', 0),
            'dexstatus': tokenData.get('dexstatus', False),
            'change1hpct': tokenData.get('change1hpct', 0),
            'tokendecimals': tokenData.get('tokendecimals'),
            'circulatingsupply': tokenData.get('circulatingsupply'),
            'tokenage': tokenData.get('tokenage'),
            'twitterlink': tokenData.get('twitterlink'),
            'telegramlink': tokenData.get('telegramlink'),
            'websitelink': tokenData.get('websitelink'),
            'firstseenat': tokenData.get('firstseenat'),
            'lastupdatedat': tokenData.get('lastupdatedat'),
            'createdat': tokenData.get('createdat'),
            'rugcount': tokenData.get('rugcount')
        }
        return PumpFunTokenData(**mappedData)

    @staticmethod
    def mapSmartMoneyTokenData(tokenData: Dict) -> SmartMoneyTokenData:
        """
        Map raw smart money token data to SmartMoneyTokenData model
        
        Args:
            tokenData: Raw token data from database
            
        Returns:
            SmartMoneyTokenData: Mapped token data
        """
        mappedData = {
            # BaseTokenData fields
            'tokenid': tokenData['tokenid'],
            'tokenname': tokenData.get('name', ''),
            'chainname': '',  # Smart money data doesn't typically have chain info
            'price': 0,  # Smart money data doesn't have price
            'marketcap': 0,  # Smart money data doesn't have marketcap
            'holders': 0,  # Smart money data doesn't have holders
            
            # SmartMoneyTokenData specific fields
            'walletaddress': tokenData['walletaddress'],
            'unprocessedpnl': tokenData.get('unprocessedpnl', 0),
            'unprocessedroi': tokenData.get('unprocessedroi', 0),
            'transactionscount': tokenData.get('transactionscount', 0),
            'amountinvested': tokenData.get('amountinvested'),
            'amounttakenout': tokenData.get('amounttakenout'),
            'remainingcoins': tokenData.get('remainingcoins'),
            'status': tokenData.get('status', 0)
        }
        return SmartMoneyTokenData(**mappedData) 