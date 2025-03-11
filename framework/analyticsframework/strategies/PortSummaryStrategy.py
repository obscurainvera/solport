from decimal import Decimal
from typing import Optional, Dict, Any, List
from framework.analyticsframework.interfaces.BaseStrategy import BaseStrategy
from framework.analyticsframework.models.BaseModels import BaseTokenData, BaseStrategyConfig, ExecutionState, TradeLog
from framework.analyticsframework.models.SourceModels import PortSummaryTokenData
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
import logging
from framework.analyticsframework.models.StrategyModels import (
     EntryType, DCARule, InvestmentInstructions
)
from framework.analyticsframework.enums.TradeTypeEnum import TradeType
from datetime import datetime, timedelta
from actions.DexscrennerAction import DexScreenerAction


logger = logging.getLogger(__name__)

class PortSummaryStrategy(BaseStrategy):
    """Strategy implementation for portfolio summary based tokens"""

    def __init__(self, analyticsHandler: AnalyticsHandler):
        self.analyticsHandler = analyticsHandler
        self.dexScreener = DexScreenerAction()
    
    def checkEntryConditions(self, tokenData: PortSummaryTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        """
        Validate entry conditions for PortSummary tokens
        Primary validation is checking if required tags are present
        """
        try:
            # Use strongly typed EntryConditions from strategy_config
            entryConditions = strategyConfig.strategyentryconditions
            
            # Check if tags are required
            if not entryConditions.requiredtags:
                logger.warning(f"No required tags defined in strategy {strategyConfig.strategyid}")
                return False

            # Convert required tags to set
            requiredTags = set(entryConditions.requiredtags)
            
            # Convert token tags string to list and then to set
            # Expecting tags in format: "TAG1,TAG2,TAG3"
            tokenTags = set(tag.strip() for tag in tokenData.tags.split(',')) if tokenData.tags else set()

            # Check if all required tags are present
            if not requiredTags.issubset(tokenTags):
                missingTags = requiredTags - tokenTags
                logger.info(f"Token {tokenData.tokenname} missing required tags: {missingTags}")
                return False

            logger.info(f"Token {tokenData.tokenname} matches all required tags: {requiredTags}")
            return True

        except Exception as e:
            logger.error(f"Error validating entry conditions: {str(e)}")
            return False
        
        
        #Implement chart conditions once we implement alchemy api
    def validateChartConditions(self, tokenData: PortSummaryTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        return True


    def executeInvestment(self, executionId: int, tokenData: PortSummaryTokenData, strategyConfig: BaseStrategyConfig) -> bool:
        """Execute investment based on investment rules"""
        try:
            investmentInstructions = strategyConfig.investmentinstructions
            
            # Get real-time price from DexScreener
            priceData = self.dexScreener.getTokenPrice(tokenData.tokenid)
            if not priceData:
                logger.error(f"Failed to get real-time price for token {tokenData.tokenid}")
                return False
                
            # Update token data with real-time price
            realTimePrice = Decimal(str(priceData.price))
            
            # Update token price for trade execution
            tokenData.price = realTimePrice
            
            if investmentInstructions.entrytype == EntryType.BULK.name:
                return self.executeBulkInvestment(executionId, tokenData, investmentInstructions)
            elif investmentInstructions.entrytype == EntryType.DCA.name:
                return self.executeDCAInvestement(executionId, tokenData, investmentInstructions)
            else:
                logger.error(f"Unknown entry type: {investmentInstructions.entrytype}")
                return False

        except Exception as e:
            logger.error(f"Error executing investment: {str(e)}")
            return False

    def executeBulkInvestment(self, executionId: int, tokenData: PortSummaryTokenData, investmentInstructions: InvestmentInstructions) -> bool:
        """Execute a bulk investment"""
        try:
            # Calculate position size
            # positionSize = min(investmentInstructions.allocated_amount, investmentInstructions.max_position_size)
            positionSize = Decimal(str(investmentInstructions.allocatedamount))
            tokenPrice = Decimal(str(tokenData.price))
            
            # Create trade record with real-time price
            tradeRecord = TradeLog(
                tradeid=None,
                executionid=executionId,
                tokenid=tokenData.tokenid,
                tokenname=tokenData.tokenname,
                tradetype=TradeType.BUY.value,
                amount=positionSize,
                tokenprice=tokenPrice,  # Using real-time price
                coins=positionSize / tokenPrice,
                description="Bulk entry position",
                createdat=datetime.now()
            )
            
            # Log trade
            return self.analyticsHandler.logTrade(tradeRecord)

        except Exception as e:
            logger.error(f"Error executing bulk investment: {str(e)}")
            return False

    def executeDCAInvestement(self, executionId: int, tokenData: PortSummaryTokenData, investmentInstructions: InvestmentInstructions) -> bool:
        """Setup DCA investment schedule with real-time price"""
        try:
            if not investmentInstructions.dcarules:
                logger.error("DCA rules not configured")
                return False

            dcaRules = investmentInstructions.dcarules
            currentTime = datetime.now()

            # Create first DCA entry with real-time price
            first_entry = TradeLog(
                trade_id=None,
                execution_id=executionId,
                token_id=tokenData.tokenid,
                token_name=tokenData.tokenname,
                trade_type=TradeType.BUY.value,
                amount=dcaRules.amountperinterval,
                token_price=tokenData.price,  # Using real-time price
                coins=dcaRules.amountperinterval / tokenData.price,
                fees=Decimal('0'),
                pnl=None,
                pnl_pct=None,
                description=f"DCA entry 1/{dcaRules.intervals}",
                created_time=currentTime
            )

            # Log first trade
            if not self.analyticsHandler.logTrade(first_entry):
                return False

            # # Schedule remaining DCA entries -  think about whether to have it here or run a separate job to monitor the execution table
            # for i in range(1, dcaRules.intervals):
            #     next_entry_time = currentTime + timedelta(
            #         minutes=dcaRules.intervaldelay * i
            #     )
                
            #     # Store DCA schedule in database
            #     self.analyticsHandler.scheduledcaentry(
            #         executionid=executionId,
            #         entrynumber=i + 1,
            #         amount=dcaRules.amountperinterval,
            #         scheduledtime=next_entry_time,
            #         pricedeviationlimit=dcaRules.pricedeviationlimit
            #     )

            return True

        except Exception as e:
            logger.error(f"Error executing DCA investment: {str(e)}")
            return False