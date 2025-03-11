"""
Marks portfolio records as inactive if they haven't been seen for more than 2 days
Runs daily to clean up tokens that are no longer tracked by smart money wallets
"""

from apscheduler.schedulers.background import BackgroundScheduler
from database.operations.sqlite_handler import SQLitePortfolioDB
from logs.logger import get_logger

logger = get_logger(__name__)

class DeactiveLostSMBalanceTokens:
    """Manages detection and deactivation of tokens no longer tracked by smart money"""
    
    def __init__(self, dbPath: str = 'portfolio.db'):
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file
        """
        self.db = SQLitePortfolioDB(dbPath)
        logger.info(f"Deactivation scheduler initialized with database: {dbPath}")

    def handleTokenDeactivation(self):
        """Process tokens that should be marked inactive"""
        try:
            # Our updated function can handle the transaction internally
            deactivatedTokens = self.db.portfolio.deactivateTokensLostSMBalance()
            logger.info(f"Deactivated {deactivatedTokens} tokens no longer tracked")
            return True
                
        except Exception as e:
            logger.error(f"Failed to process token deactivation: {e}")
            return False

    