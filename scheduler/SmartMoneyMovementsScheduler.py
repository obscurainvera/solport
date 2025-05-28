"""
Scheduler for processing smart money wallet movements for wallets with PnL > 100K

Runs periodically to fetch and process wallet movements for high-value wallets
"""
from apscheduler.schedulers.background import BackgroundScheduler
from actions.SmartMoneyMovementsAction import SmartMoneyMovementsAction
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.smartmoneywallets.SmartMoneyWalletsHandler import SmartMoneyWalletsHandler
from logs.logger import get_logger
import time
import random
from decimal import Decimal

logger = get_logger(__name__)

class SmartMoneyMovementsScheduler:
    """Manages smart money movements data collection and scheduling"""
    
    def __init__(self, dbPath: str = 'portfolio.db'):
        """
        Initialize scheduler with database instance
        
        Args:
            dbPath: Path to SQLite database file
        """
        self.db = SQLitePortfolioDB(dbPath)
        self.action = SmartMoneyMovementsAction(self.db)
        self.wallets_handler = SmartMoneyWalletsHandler(self.db.conn_manager)
        logger.info(f"Smart Money Movements scheduler initialized with database: {dbPath}")

    def handleSmartMoneyMovementsUpdate(self, pnl_threshold: float = 100000):
        """
        Execute smart money movements update for wallets with PnL > threshold
        """
        start_time = time.time()
        logger.info(f"Starting smart money movements update for wallets with PnL > {pnl_threshold}")
        
        # Get all wallets from the database
        allSmartMoneyWallets = self.wallets_handler.getActiveSmartMoneyWallets()
        
        logger.info(f"Found {len(allSmartMoneyWallets)} wallets")
        
        # Process each wallet
        processed_count = 0
        success_count = 0
        failed_count = 0
        
        for wallet in allSmartMoneyWallets:
            walletAddress = wallet['walletaddress']
            try:
                logger.info(f"Processing wallet {walletAddress} with PnL {wallet['profitandloss']}")
                
                # Process wallet movements
                success = self.action.processWalletMovements(walletAddress)
                
                if success:
                    success_count += 1
                    logger.info(f"Successfully processed wallet {walletAddress}")
                else:
                    failed_count += 1
                    logger.error(f"Failed to process wallet {walletAddress}")
                
                processed_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Error processing wallet {walletAddress}: {str(e)}")
        
        execution_time = time.time() - start_time
        logger.info(f"Smart money movements update completed in {execution_time:.2f} seconds")
        logger.info(f"Processed {processed_count} wallets: {success_count} successful, {failed_count} failed")
        
        return {
            "walletsProcessed": processed_count,
            "walletsSuccessful": success_count,
            "walletsFailed": failed_count,
            "executionTime": f"{execution_time:.2f}s"
        }
