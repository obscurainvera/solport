"""
Takes all the token help by smart money through portfolio summary api and persists them to the database

Runs every four hours

"""
from apscheduler.schedulers.background import BackgroundScheduler
from actions.portfolio.PortfolioSummaryAction import PortfolioSummaryAction
from config.Constants import PORTFOLIO_CATEGORIES
from config.Security import COOKIE_MAP, isValidCookie
from database.operations.sqlite_handler import SQLitePortfolioDB
from logs.logger import get_logger
import time
import random
from actions.portfolio.PortfolioTaggerAction import PortfolioTaggerAction
logger = get_logger(__name__)

class PortfolioScheduler:
    """Manages portfolio data collection and scheduling"""
    
    def __init__(self, dbPath: str = 'portfolio.db'):
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file
        """
        self.db = SQLitePortfolioDB(dbPath)
        self.action = PortfolioSummaryAction(self.db)
        logger.info(f"Portfolio scheduler initialized with database: {dbPath}")

    def handlePortfolioSummaryUpdate(self):
        """Execute portfolio actions if valid cookie exists"""
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('portfolio', {})
            if isValidCookie(cookie, 'portfolio')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for portfolio actions")
            return

        for cookie in validCookies:
            try:
                logger.debug(f"Using cookie: {cookie[:15]}...")
                
                # Iterate through portfolio categories
                for category in PORTFOLIO_CATEGORIES:
                    self.action.getPortfolioSummaryAPIData(
                        cookie=cookie,
                        marketAge=category["market_age"],
                        pnlWallet=category["pnl_wallet"],
                        ownership=category["ownership"]
                    )
                    # Sleep between API calls
                    delay = random.uniform(10, 15)
                    logger.info(f"Sleeping for {delay} seconds")
                    time.sleep(delay)
                    logger.info("Sleep completed")
                
            except Exception as e:
                logger.error(f"Failed to execute action for market age {category['market_age']}: {str(e)}")

        PortfolioTaggerAction(self.db).addTagsToActivePortSummaryTokens()