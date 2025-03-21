# scheduler/smwallet_behaviour_scheduler.py
from database.operations.sqlite_handler import SQLitePortfolioDB
from actions.SmartMoneyWalletBehaviourAction import SmartMoneyWalletBehaviourAction
from logs.logger import get_logger
from typing import Optional
logger = get_logger(__name__)

class SMWalletBehaviourScheduler:
    """Schedules Smart Money Wallet Behaviour analysis"""
    
    def __init__(self, dbPath: str = 'portfolio.db'):
        self.db = SQLitePortfolioDB(dbPath)
        self.action = SmartMoneyWalletBehaviourAction(self.db)
        logger.info(f"Smart Money Wallet Behaviour scheduler initialized with database: {dbPath}")

    def runAnalysis(self, walletAddress: Optional[str] = None):
        """Run the Smart Money Wallet Behaviour analysis, optionally for a specific wallet"""
        try:
            result = self.action.analyzeWalletBehaviour(walletAddress)
            if result:
                logger.info(f"Smart Money Wallet Behaviour analysis executed successfully{' for wallet ' + walletAddress if walletAddress else ''}")
                return True
            logger.warning(f"Smart Money Wallet Behaviour analysis completed with no data processed{' for wallet ' + walletAddress if walletAddress else ''}")
            return False
        except Exception as e:
            logger.error(f"Failed to execute Smart Money Wallet Behaviour analysis{' for wallet ' + walletAddress if walletAddress else ''}: {str(e)}")
            return False