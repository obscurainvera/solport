from typing import List, Optional, Tuple, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
import time
from framework.analyticsframework.enums.ExecutionStatusEnum import ExecutionStatus
from framework.analyticsframework.models.BaseModels import ExecutionState, BaseStrategyConfig, BaseTokenData
from framework.analyticsframework.StrategyFramework import StrategyFramework
from framework.analyticsframework.models.StrategyModels import (
    ProfitTarget,RiskManagementInstructions
)
from logs.logger import get_logger
from framework.analyticsframework.models.StrategyModels import ProfitTakingInstructions
from actions.DexscrennerAction import DexScreenerAction

logger = get_logger(__name__)

class ExecutionMonitor:
    def __init__(self, strategyFramework: StrategyFramework):
        self.strategyFramework = strategyFramework
        self.dexScreener = DexScreenerAction()

    def monitorActiveExecutions(self):
        """Monitor and update active executions"""
        # Initialize stats
        stats = {
            "executionsProcessed": 0,
            "stopLossesTriggered": 0,
            "profitTargetsHit": 0,
            "errors": 0
        }
         
        try:
            # Get all active executions with their configs
            activeExecutions = self.strategyFramework.getActiveExecutions()
            
            if not activeExecutions:
                logger.info("No active executions found to monitor")
                return stats
            
            logger.info(f"Found {len(activeExecutions)} active executions to process")
            
            for executionState, strategyConfig in activeExecutions:
                try:
                    logger.info(f"Processing execution for token ID: {executionState.tokenid}, Name: {executionState.tokenname}")
                    success = self.processExecution(executionState, strategyConfig)
                    stats["executionsProcessed"] += 1
                    # Update stats based on execution result if available
                    if isinstance(success, dict):
                        if success.get("stopLossTriggered", False):
                            stats["stopLossesTriggered"] += 1
                        if success.get("profitTargetHit", False):
                            stats["profitTargetsHit"] += 1
                except Exception as e:
                    logger.error(f"Error processing execution {executionState.executionid}: {str(e)}")
                    stats["errors"] += 1

            logger.info(f"Monitoring cycle completed: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error monitoring executions: {str(e)}")
            return stats

    def handleStopLoss(self, executionState: ExecutionState, tokenData: BaseTokenData, 
                       strategyConfig: BaseStrategyConfig, currentPrice: Decimal) -> bool:
        """
        Handle stop loss execution for a token
        
        Args:
            executionState: Current execution state
            tokenData: Token data with current price
            strategyConfig: Strategy configuration
            currentPrice: Current token price
            
        Returns:
            bool: True if stop loss was successfully executed
        """
        logger.warning(f"Stop loss triggered for execution {executionState.executionid}")
        
        # Create a full exit target
        stopLossTarget = ProfitTarget(
            pricepct=Decimal('0'),  # Not relevant for stop loss
            sizepct=Decimal('100')  # Full position exit
        )
        
        # Execute stop loss
        success = self.strategyFramework.takeProfits(
            executionState=executionState,
            tokenData=tokenData,
            strategyConfig=strategyConfig,
            target=stopLossTarget,
            currentPrice=currentPrice
        )
        
        if success:
            logger.info(f"Successfully executed stop loss for execution {executionState.executionid}")
        else:
            logger.error(f"Failed to execute stop loss for execution {executionState.executionid}")
            
        return success

    def processExecution(self, executionState: ExecutionState, strategyConfig: BaseStrategyConfig):
        """Process a single execution"""
        try:
            # Get current price
            priceData = self.dexScreener.getTokenPrice(executionState.tokenid)
            if not priceData:
                logger.warning(f"Could not get price for token {executionState.tokenid}")
                return

            currentPrice = Decimal(str(priceData.price))

            # Create minimal token data object for profit taking
            tokenData = BaseTokenData(
                tokenid=executionState.tokenid,
                tokenname=executionState.tokenname,
                price=currentPrice,
                marketcap=Decimal(str(getattr(priceData, 'marketcap', '0'))),
                holders=getattr(priceData, 'holders', 0),
                chainname=getattr(priceData, 'chainname', 'solana')
            )

            # Check stop loss first
            if self.strategyFramework.isStopLossHit(executionState, currentPrice, strategyConfig.riskmanagementinstructions):
                self.handleStopLoss(executionState, tokenData, strategyConfig, currentPrice)
                return  # Exit early after stop loss

            # Continue with profit target checks if stop loss not triggered
            profitTarget = self.strategyFramework.getProfitTargets(
                executionState=executionState,
                currentPrice=currentPrice,
                profitTakingInstructions=strategyConfig.profittakinginstructions
            )

            if profitTarget:
                logger.info(
                    f"Profit target hit for execution {executionState.executionid}: "
                    f"{profitTarget.pricepct}%"
                )
                
                # Execute profit taking with objects we already have
                success = self.strategyFramework.takeProfits(
                    executionState=executionState,
                    tokenData=tokenData,
                    strategyConfig=strategyConfig,
                    target=profitTarget,
                    currentPrice=currentPrice
                )
                
                if success:
                    logger.info(
                        f"Successfully executed profit taking for execution "
                        f"{executionState.executionid}"
                    )
                else:
                    logger.error(
                        f"Failed to execute profit taking for execution "
                        f"{executionState.executionid}"
                    )

        except Exception as e:
            logger.error(f"Error processing execution {executionState.executionid}: {str(e)}")

