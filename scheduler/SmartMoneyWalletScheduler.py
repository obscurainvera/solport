"""
Scheduler to persist all the smart money wallets data from the API
"""

from database.operations.sqlite_handler import SQLitePortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from actions.SmartMoneyWalletsAction import SmartMoneyWalletsAction
import time
import random

logger = get_logger(__name__)

class SmartMoneyWalletsScheduler:
    """Manages smart money wallets data collection and analysis"""
    
    def __init__(self, dbPath: str = 'portfolio.db'):
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file
        """
        self.db = SQLitePortfolioDB(dbPath)
        self.action = SmartMoneyWalletsAction(self.db)
        logger.info(f"Smart Money Wallets scheduler initialized with database: {dbPath}")

    def executeActions(self):
        """Process smart money wallets analysis"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('smartmoneywallets', {})
            if isValidCookie(cookie, 'smartmoneywallets')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for smart money wallets API")
            return False

        for cookie in validCookies:
            try:
                logger.info(f"Using cookie: {cookie[:15]}...")
                
                success = self.action.getAllSmartMoneyWallets(cookie=cookie)
                
                if success:
                    logger.info("Successfully analyzed wallet behaviour")
                else:
                    logger.warning("Failed to analyze wallet behaviour")
                
                # Add delay between requests
                delay = random.uniform(2.0, 5.0)
                time.sleep(delay)
                
            except Exception as e:
                logger.error(f"Failed to execute wallet behaviour analysis: {e}")
                continue
                
        return True 