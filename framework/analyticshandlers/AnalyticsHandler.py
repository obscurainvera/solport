from database.operations.base_handler import BaseSQLiteHandler
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
from datetime import datetime
from logs.logger import get_logger
from framework.analyticsframework.enums.StrategyStatusEnum import StrategyStatus
from framework.analyticsframework.enums.ExecutionStatusEnum import ExecutionStatus
from framework.analyticsframework.enums.TradeTypeEnum import TradeType
from framework.analyticsframework.enums.PushSourceEnum import PushSource
from framework.analyticsframework.models.BaseModels import ExecutionState, BaseStrategyConfig
from framework.analyticsframework.models.StrategyModels import InvestmentInstructions, ProfitTakingInstructions,RiskManagementInstructions
from framework.analyticsframework.models.BaseModels import TradeLog
import json

logger = get_logger(__name__)

class AnalyticsHandler(BaseSQLiteHandler):
    """Handles strategy analytics data operations"""
    
    def __init__(self, conn_manager):
        super().__init__(conn_manager)
        self._createTables()

    
    def _createTables(self):
        """Creates all required tables for strategy analytics"""
        with self.conn_manager.transaction() as cursor:
            # Strategy Configuration
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategyconfig (
                    strategyid INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategyname TEXT NOT NULL,
                    source TEXT NOT NULL,
                    description TEXT,
                    strategyentryconditions TEXT NOT NULL,
                    chartconditions TEXT,
                    investmentinstructions TEXT NOT NULL,
                    profittakinginstructions TEXT NOT NULL,
                    riskmanagementinstructions TEXT NOT NULL,
                    moonbaginstructions TEXT,
                    additionalinstructions TEXT,
                    status INTEGER DEFAULT 1,
                    active INTEGER DEFAULT 1,
                    superuser INTEGER DEFAULT 0,
                    isjournalstrategy INTEGER DEFAULT 1,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Strategy execution table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategyexecution (
                    executionid INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategyid INTEGER NOT NULL,
                    description TEXT,
                    tokenid TEXT NOT NULL,
                    tokenname TEXT NOT NULL,
                    avgentryprice DECIMAL,
                    remainingcoins DECIMAL,
                    allotedamount DECIMAL NOT NULL,
                    investedamount DECIMAL,
                    amounttakenout DECIMAL,
                    realizedpnl DECIMAL,
                    realizedpnlpercent DECIMAL,
                    recordedtokenage INTEGER,
                    completedtokenage INTEGER,
                    status INTEGER NOT NULL,
                    notes TEXT,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (strategyid) REFERENCES strategyconfig(strategyid)
                )
            ''')
            
            # Trade log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS tradelog (
                    tradeid INTEGER PRIMARY KEY AUTOINCREMENT,
                    executionid INTEGER NOT NULL,
                    tokenid TEXT NOT NULL,
                    tokenname TEXT NOT NULL,
                    tradetype TEXT NOT NULL,
                    amount DECIMAL NOT NULL,
                    tokenprice DECIMAL NOT NULL,
                    coins DECIMAL NOT NULL,
                    description TEXT,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (executionid) REFERENCES strategyexecution(executionid)
                )
            ''')
            
            logger.info("Analytics tables created successfully")

    def createStrategy(self, strategyConfig: Dict[str, Any]) -> Optional[int]:
        """Create a new strategy configuration"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    INSERT INTO strategyconfig (
                        strategyname, source, description,
                        strategyentryconditions, chartconditions, investmentinstructions,
                        profittakinginstructions, riskmanagementinstructions,
                        moonbaginstructions, additionalinstructions, status, active, superuser, isjournalstrategy, createdat, updatedat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategyConfig['strategyname'],
                    strategyConfig['source'],
                    strategyConfig.get('description'),
                    strategyConfig['strategyentryconditions'],
                    strategyConfig.get('chartconditions'),
                    strategyConfig['investmentinstructions'],
                    strategyConfig['profittakinginstructions'],
                    strategyConfig['riskmanagementinstructions'],
                    strategyConfig.get('moonbaginstructions'),
                    strategyConfig.get('additionalinstructions'),
                    strategyConfig.get('status', StrategyStatus.ACTIVE.value),
                    strategyConfig.get('active', True),
                    1 if strategyConfig.get('superuser', False) else 0,
                    1 if strategyConfig.get('isjournalstrategy', False) else 0,
                    strategyConfig.get('createdat', datetime.now()),
                    strategyConfig.get('updatedat', datetime.now())
                ))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to create strategy: {str(e)}")
            return None

    def getAllActiveStrategies(self, source: str, pushSource: PushSource = PushSource.SCHEDULER) -> List[Dict]:
        """
        Get all active strategies for a specific source
        
        Args:
            source: Source type to filter strategies
            pushSource: Source that pushed the token into the framework
            
        Returns:
            List[Dict]: List of active strategies for the source
        """
        try:
            with self.conn_manager.transaction() as cursor:
                # If token was pushed via API, include only superuser strategies
                # If token was pushed via Scheduler, include only non-superuser strategies
                if pushSource == PushSource.API:
                    cursor.execute('''
                        SELECT * FROM strategyconfig 
                        WHERE source = ? AND active = 1 AND superuser = 1
                    ''', (source,))
                else:
                    cursor.execute('''
                        SELECT * FROM strategyconfig 
                        WHERE source = ? AND active = 1 AND superuser = 0
                    ''', (source,))
                
                columns = [col[0] for col in cursor.description]
                strategies = []
                
                for row in cursor.fetchall():
                    strategy_dict = dict(zip(columns, row))
                    # Convert superuser from int to bool
                    strategy_dict['superuser'] = bool(strategy_dict['superuser'])
                    strategies.append(strategy_dict)
                
                return strategies
        except Exception as e:
            logger.error(f"Failed to get active strategies: {str(e)}")
            return []

    def recordExecution(self, executionData: ExecutionState) -> Optional[int]:
        """
        Record a new strategy execution
        
        Args:
            executionData: Execution state data
            
        Returns:
            Optional[int]: Execution ID if successful, None otherwise
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    INSERT INTO strategyexecution (
                        strategyid, tokenid, tokenname, status, allotedamount,
                        description, remainingcoins, investedamount, avgentryprice,
                        realizedpnl, realizedpnlpercent, recordedtokenage, notes, createdat, updatedat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    executionData.strategyid,
                    executionData.tokenid,
                    executionData.tokenname,
                    executionData.status.value,
                    str(executionData.allotedamount),
                    executionData.description,
                    str(executionData.remainingcoins) if executionData.remainingcoins is not None else None,
                    str(executionData.investedamount) if executionData.investedamount is not None else None,
                    str(executionData.avgentryprice) if executionData.avgentryprice is not None else None,
                    str(executionData.realizedpnl) if executionData.realizedpnl is not None else None,
                    str(executionData.realizedpnlpercent) if executionData.realizedpnlpercent is not None else None,
                    executionData.recordedtokenage if hasattr(executionData, 'recordedtokenage') else None,
                    executionData.notes,
                    executionData.createdat,
                    executionData.updatedat
                ))
                
                executionId = cursor.lastrowid
                logger.info(f"Recorded execution with ID: {executionId}")
                return executionId
                
        except Exception as e:
            logger.error(f"Failed to record execution: {str(e)}")
            return None

    def logTrade(self, tradeData: TradeLog) -> Optional[int]:
        """
        Log a trade for an execution
        
        Args:
            tradeData: Trade log data
            
        Returns:
            Optional[int]: Trade ID if successful, None otherwise
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    INSERT INTO tradelog (
                        executionid, tokenid, tokenname, tradetype,
                        amount, tokenprice, coins, description,
                        createdat, updatedat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    tradeData.executionid,
                    tradeData.tokenid,
                    tradeData.tokenname,
                    tradeData.tradetype,
                    str(tradeData.amount),
                    str(tradeData.tokenprice),
                    str(tradeData.coins),
                    tradeData.description,
                    datetime.now(),
                    datetime.now()
                ))
                
                tradeId = cursor.lastrowid
                logger.info(f"Logged trade with ID: {tradeId}")
                return tradeId
                
        except Exception as e:
            logger.error(f"Failed to log trade: {str(e)}")
            return None

    def getStrategyExecutions(self, strategyId: int) -> List[Dict]:
        """Get all executions for a strategy"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT * FROM strategyexecution WHERE strategyid = ?
                ''', (strategyId,))
                
                columns = [col[0] for col in cursor.description]
                executions = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return executions
        except Exception as e:
            logger.error(f"Failed to get strategy executions: {str(e)}")
            return []

    def getExecutionTrades(self, executionId: int) -> List[Dict]:
        """Get all trades for an execution"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT * FROM tradelog WHERE executionid = ?
                ''', (executionId,))
                
                columns = [col[0] for col in cursor.description]
                trades = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return trades
        except Exception as e:
            logger.error(f"Failed to get execution trades: {str(e)}")
            return []

    def updateExecutionPnl(self, executionId: int, realizedPnl: Decimal, realizedPnlPct: Decimal) -> bool:
        """Update realized PnL for an execution"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    UPDATE strategyexecution
                    SET realizedpnl = ?, realizedpnlpercent = ?, updatedat = ?
                    WHERE executionid = ?
                ''', (
                    str(realizedPnl),
                    str(realizedPnlPct),
                    datetime.now(),
                    executionId
                ))
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Failed to update execution PnL: {str(e)}")
            return False

    def updateStrategy(self, strategyId: int, updateData: Dict[str, Any]) -> bool:
        """Update strategy configuration"""
        try:
            if not updateData:
                logger.warning("No update data provided")
                return False
                
            # Build update query
            setClause = ", ".join([f"{key} = ?" for key in updateData.keys()])
            values = list(updateData.values())
            values.append(strategyId)
            
            with self.conn_manager.transaction() as cursor:
                cursor.execute(f'''
                    UPDATE strategyconfig
                    SET {setClause}
                    WHERE strategyid = ?
                ''', values)
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Updated strategy {strategyId}")
                else:
                    logger.warning(f"No strategy found with ID {strategyId}")
                    
                return success
        except Exception as e:
            logger.error(f"Failed to update strategy: {str(e)}")
            return False

    def updateExecutionStatus(self, executionId: int, status: ExecutionStatus) -> bool:
        """Update execution status"""
        try:
            with self.conn_manager.transaction() as cursor:
                # Convert enum value to integer
                statusValue = int(status.value)
                
                cursor.execute('''
                    UPDATE strategyexecution
                    SET status = ?, updatedat = ?
                    WHERE executionid = ?
                ''', (
                    statusValue,
                    datetime.now(),
                    executionId
                ))
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Updated execution {executionId} status to {status.name}")
                else:
                    logger.warning(f"No execution found with ID {executionId}")
                    
                return success
        except Exception as e:
            logger.error(f"Failed to update execution status: {str(e)}")
            return False

    def updateExecution(self, executionId: int, investedAmount: Decimal = None, 
                        remainingCoins: Decimal = None, avgEntryPrice: Decimal = None,
                        status: ExecutionStatus = None, amountTakenOut: Decimal = None,
                        recordedTokenAge: int = None, completedTokenAge: int = None) -> bool:
        """Update execution details"""
        try:
            # Build update query parts
            updateParts = []
            values = []
            
            if investedAmount is not None:
                updateParts.append("investedamount = ?")
                values.append(str(investedAmount))
                
            if remainingCoins is not None:
                updateParts.append("remainingcoins = ?")
                values.append(str(remainingCoins))
                
            if avgEntryPrice is not None:
                updateParts.append("avgentryprice = ?")
                values.append(str(avgEntryPrice))
                
            if amountTakenOut is not None:
                updateParts.append("amounttakenout = ?")
                values.append(str(amountTakenOut))
                
            if recordedTokenAge is not None:
                updateParts.append("recordedtokenage = ?")
                values.append(recordedTokenAge)
                
            if completedTokenAge is not None:
                updateParts.append("completedtokenage = ?")
                values.append(completedTokenAge)
                
            if status is not None:
                updateParts.append("status = ?")
                # Convert enum value to integer
                values.append(int(status.value))
                
            # Always update timestamp
            updateParts.append("updatedat = ?")
            values.append(datetime.now())
            
            # Add execution ID
            values.append(executionId)
            
            if not updateParts:
                logger.warning("No update data provided")
                return False
                
            # Execute update
            with self.conn_manager.transaction() as cursor:
                cursor.execute(f'''
                    UPDATE strategyexecution
                    SET {", ".join(updateParts)}
                    WHERE executionid = ?
                ''', values)
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Updated execution {executionId}")
                else:
                    logger.warning(f"No execution found with ID {executionId}")
                    
                return success
        except Exception as e:
            logger.error(f"Failed to update execution: {str(e)}")
            return False

    def getActiveExecutionsWithConfig(self) -> List[Tuple[ExecutionState, BaseStrategyConfig]]:
        """Get all active executions with their strategy configurations"""
        try:
            with self.conn_manager.transaction() as cursor:
                # Convert enum values to integers before using in the query
                activeStatus = int(ExecutionStatus.ACTIVE.value)
                investedStatus = int(ExecutionStatus.INVESTED.value)
                
                # Use table aliases and explicitly select columns with table prefixes
                cursor.execute('''
                    SELECT 
                        e.executionid, e.strategyid, e.description AS execution_description, 
                        e.tokenid, e.tokenname, e.avgentryprice, e.remainingcoins, 
                        e.allotedamount, e.investedamount, e.amounttakenout, 
                        e.realizedpnl, e.realizedpnlpercent, e.status AS execution_status, 
                        e.notes, e.createdat AS execution_createdat, e.updatedat AS execution_updatedat,
                        
                        s.strategyid, s.strategyname, s.source, s.description AS strategy_description,
                        s.strategyentryconditions, s.chartconditions, s.investmentinstructions,
                        s.profittakinginstructions, s.riskmanagementinstructions, 
                        s.moonbaginstructions, s.additionalinstructions, 
                        s.status AS strategy_status, s.active, 
                        s.createdat AS strategy_createdat, s.updatedat AS strategy_updatedat
                    FROM strategyexecution e
                    JOIN strategyconfig s ON e.strategyid = s.strategyid
                    WHERE e.status IN (?, ?)
                ''', (activeStatus, investedStatus))
                
                rows = cursor.fetchall()
                if not rows:
                    return []
                    
                # Get column names with their aliases
                columns = [col[0] for col in cursor.description]
                
                result = []
                for row in rows:
                    # Create a dictionary with all column values
                    rowDict = dict(zip(columns, row))
                    
                    # Create ExecutionState object
                    execution = ExecutionState(
                        executionid=rowDict['executionid'],
                        strategyid=rowDict['strategyid'],
                        tokenid=rowDict['tokenid'],
                        tokenname=rowDict['tokenname'],
                        status=ExecutionStatus.fromValue(rowDict['execution_status']),
                        allotedamount=Decimal(str(rowDict['allotedamount'])),
                        description=rowDict['execution_description'],
                        remainingcoins=Decimal(str(rowDict['remainingcoins'])) if rowDict['remainingcoins'] else None,
                        investedamount=Decimal(str(rowDict['investedamount'])) if rowDict['investedamount'] else None,
                        avgentryprice=Decimal(str(rowDict['avgentryprice'])) if rowDict['avgentryprice'] else None,
                        amounttakenout=Decimal(str(rowDict['amounttakenout'])) if rowDict['amounttakenout'] not in (None, '') else Decimal('0'),
                        realizedpnl=Decimal(str(rowDict['realizedpnl'])) if rowDict['realizedpnl'] else None,
                        realizedpnlpercent=Decimal(str(rowDict['realizedpnlpercent'])) if rowDict['realizedpnlpercent'] else None,
                        notes=rowDict['notes'],
                        createdat=rowDict['execution_createdat'],
                        updatedat=rowDict['execution_updatedat']
                    )
                    
                    # Create BaseStrategyConfig object
                    strategy = BaseStrategyConfig(
                        strategyid=rowDict['strategyid'],
                        strategyname=rowDict['strategyname'],
                        source=rowDict['source'],
                        description=rowDict['strategy_description'],
                        strategyentryconditions=rowDict['strategyentryconditions'],
                        chartconditions=rowDict['chartconditions'],
                        investmentinstructions=rowDict['investmentinstructions'],
                        profittakinginstructions=rowDict['profittakinginstructions'],
                        riskmanagementinstructions=rowDict['riskmanagementinstructions'],
                        moonbaginstructions=rowDict['moonbaginstructions'],
                        additionalinstructions=json.loads(rowDict['additionalinstructions']) if rowDict['additionalinstructions'] else None,
                        status=rowDict['strategy_status'],
                        active=bool(rowDict['active']),
                        createdat=rowDict['strategy_createdat'],
                        updatedat=rowDict['strategy_updatedat']
                    )
                    
                    result.append((execution, strategy))
                    
                return result
                
        except Exception as e:
            logger.error(f"Failed to get active executions: {str(e)}")
            return []

    def getActiveStrategiesForSource(self, source: str) -> List[Dict]:
        """
        Get all active strategies for a specific source type
        
        Args:
            source: Source type to filter strategies (e.g., 'PORTSUMMARY', 'ATTENTION')
            
        Returns:
            List[Dict]: List of active strategies for the source
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT * FROM strategyconfig 
                    WHERE source = ? AND active = 1
                ''', (source,))
                
                columns = [col[0] for col in cursor.description]
                strategies = []
                
                for row in cursor.fetchall():
                    strategy_dict = dict(zip(columns, row))
                    # Convert superuser from int to bool
                    strategy_dict['superuser'] = bool(strategy_dict['superuser'])
                    strategies.append(strategy_dict)
                
                return strategies
        except Exception as e:
            logger.error(f"Failed to get active strategies for source {source}: {str(e)}")
            return []

    def getStrategyById(self, strategyId: int) -> Optional[Dict]:
        """Get strategy by ID"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT * FROM strategyconfig WHERE strategyid = ?
                ''', (strategyId,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
                
        except Exception as e:
            logger.error(f"Failed to get strategy by ID: {str(e)}")
            return None

    def getExecutionById(self, executionId: int) -> Optional[Dict]:
        """Get execution by ID"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT * FROM strategyexecution WHERE executionid = ?
                ''', (executionId,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                columns = [col[0] for col in cursor.description]
                return dict(zip(columns, row))
                
        except Exception as e:
            logger.error(f"Failed to get execution by ID: {str(e)}")
            return None

    def getExecutionsForTokenAndStrategy(self, tokenId: str, strategyId: int) -> List[Dict]:
        """
        Get all executions for a specific token and strategy
        
        Args:
            tokenId: Token identifier
            strategyId: Strategy identifier
            
        Returns:
            List[Dict]: List of executions matching the criteria
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    SELECT * FROM strategyexecution 
                    WHERE tokenid = ? AND strategyid = ?
                    ORDER BY createdat DESC
                ''', (tokenId, strategyId))
                
                columns = [col[0] for col in cursor.description]
                executions = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                return executions
        except Exception as e:
            logger.error(f"Failed to get executions for token {tokenId} and strategy {strategyId}: {str(e)}")
            return [] 