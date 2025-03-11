"""
Persists all the top pnl tokens of sm wallets
"""
from apscheduler.schedulers.background import BackgroundScheduler
from actions.SMWalletTopPNLTokenAction import SMWalletTopPNLTokenAction
from config.Security import COOKIE_MAP, isValidCookie
from database.operations.sqlite_handler import SQLitePortfolioDB
from logs.logger import get_logger
import time
import random

logger = get_logger(__name__)

class SMWalletTopPnlTokenScheduler:
    """Manages top PNL token data collection and scheduling"""
    
    def __init__(self, dbPath: str = 'portfolio.db'):
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file
        """
        self.db = SQLitePortfolioDB(dbPath)
        self.action = SMWalletTopPNLTokenAction(self.db)
        logger.info(f"Top PNL token scheduler initialized with database: {dbPath}")

    def persistAllTopPNLTokensForHighPNLSMWallets(self):
        """Execute top PNL token actions if valid cookie exists"""
        # Get valid cookies for top PNL token action
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('smwallettoppnltoken', {})
            if isValidCookie(cookie, 'smwallettoppnltoken')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for top PNL token actions")
            return False

        try:
            # Get all active wallets from wallet_behaviour table
            activeWallets = self.db.smartMoneyWallets.getAllHighPnlSmartMoneyWallets()
            
            if not activeWallets:
                logger.warning("No active wallets found for analysis")
                return False

            for cookie in validCookies:
                try:
                    logger.info(f"Using cookie: {cookie[:15]}...")
                    
                    # Process each wallet
                    for wallet in activeWallets:
                        try:
                            self.action.persistAllTopPNLTokensForASMWallet(
                                cookie=cookie,
                                walletAddress=wallet.get('walletAddress'),
                                lookbackDays=180
                            )
                            
                            # Sleep between API calls
                            delay = random.uniform(20, 50)
                            logger.info(f"Sleeping for {delay} seconds")
                            time.sleep(delay)
                            
                        except Exception as e:
                            logger.error(f"Failed to process wallet {wallet['walletaddress']}: {str(e)}")
                            continue
                    
                except Exception as e:
                    logger.error(f"Failed to execute action with cookie: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error in top PNL token processing: {e}")
            return False 