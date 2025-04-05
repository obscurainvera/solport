"""
Monitors active strategy executions for profit targets and stop losses

Runs every minute to check current prices against strategy conditions
"""

from framework.analyticsframework.ExecutionMonitor import ExecutionMonitor
from framework.analyticsframework.StrategyFramework import StrategyFramework
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from database.operations.sqlite_handler import SQLitePortfolioDB
from logs.logger import get_logger
import time

logger = get_logger(__name__)

class ExecutionMonitorScheduler:
    """Manages monitoring of active strategy executions"""
    
    def __init__(self, dbPath: str = 'portfolio.db'):
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file
        """
        self.db = SQLitePortfolioDB(dbPath)
        self.analyticsHandler = AnalyticsHandler(self.db)
        self.strategyFramework = StrategyFramework()
        self.monitor = ExecutionMonitor()
        logger.info(f"Execution monitor scheduler initialized with database: {dbPath}")

    def handleActiveExecutionsMonitoring(self):
        """Monitor all active executions for profit targets and stop losses"""
        try:
            logger.info("Starting active executions monitoring...")
            
            # Monitor active executions
            monitoringStats = self.monitor.monitorActiveExecutions()
            
            if monitoringStats:
                logger.info(f"Monitoring completed: {monitoringStats}")
                return True
            
            logger.warning("No active executions to monitor")
            return False
            
        except Exception as e:
            logger.error(f"Failed to monitor active executions: {e}")
            return False 