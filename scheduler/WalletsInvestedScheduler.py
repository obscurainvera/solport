"""
Takes all the wallets invested in a specific token and persists them to the database

Scheduler not added till now
"""
from actions.WalletsInvestedAction import WalletsInvestedAction
from config.Security import COOKIE_MAP, isValidCookie
from database.operations.sqlite_handler import SQLitePortfolioDB
from logs.logger import get_logger
import time
import random

logger = get_logger(__name__)

class WalletsInvestedScheduler:
    """Manages token analysis data collection and scheduling"""
    
    def __init__(self, db_path: str = 'portfolio.db'):
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file
        """
        self.db = SQLitePortfolioDB(db_path)
        self.action = WalletsInvestedAction(self.db)
        logger.info(f"Wallets Invested Analysis scheduler initialized with database: {db_path}")

    def handleWalletsInvestedInPortSummaryTokens(self):
        """Execute token analysis actions if valid cookie exists"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('walletsinvested', {})
            if isValidCookie(cookie, 'walletsinvested')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for wallets invested actions")
            return

        for cookie in validCookies:
            try:
                logger.debug(f"Using cookie: {cookie[:15]}...")
                
                # Get active tokens using the new method
                activeTokens = self.db.portfolio.getActivePortfolioTokens()
                logger.debug(f"Found {len(activeTokens)} active tokens for analysis")
                
                # Process each active token
                for token in activeTokens:
                    try:
                        logger.debug(f"Processing wallets invested analysis for {token['tokenid']} - {token['name']}")
                        self.action.fetchAndPersistWalletsInvestedInASpecificToken(
                            cookie=cookie,
                            tokenId=token['tokenid'],
                            portsummaryId=token['portsummaryid']
                        )
                        
                        # Sleep between API calls
                        delay = random.uniform(10,30)
                        logger.info(f"Sleeping for {delay} seconds")
                        time.sleep(delay)
                        logger.info("Sleep completed")
                        
                    except Exception as e:
                        logger.error(f"Failed to process token {token['tokenid']}: {str(e)}")
                        continue
                
            except Exception as e:
                logger.error(f"Failed to execute wallets invested analysis action: {str(e)}") 