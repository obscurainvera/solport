from database.operations.base_handler import BaseSQLiteHandler
from typing import Dict, Optional, List, Tuple
import sqlite3
from datetime import datetime
from logs.logger import get_logger

logger = get_logger(__name__)

class SmartMoneyMovementsHandler(BaseSQLiteHandler):
    """
    Handler for smart money movements data.
    Manages daily token and USD changes for smart money wallets.
    """
    
    def __init__(self, conn_manager):
        super().__init__(conn_manager)
        self._create_tables()

    def _create_tables(self):
        """Create smartmoneymovements and smartmoneymovementsbatch tables if they don't exist"""
        with self.conn_manager.transaction() as cursor:
            # Create smartmoneymovements table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS smartmoneymovements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    walletaddress TEXT NOT NULL,
                    tokenaddress TEXT NOT NULL,
                    buytokenchange DECIMAL NOT NULL DEFAULT 0,
                    selltokenchange DECIMAL NOT NULL DEFAULT 0,
                    buyusdchange DECIMAL NOT NULL DEFAULT 0,
                    sellusdchange DECIMAL NOT NULL DEFAULT 0,
                    buytokenname TEXT,
                    selltokenname TEXT,
                    date DATE NOT NULL,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(walletaddress, tokenaddress, date)
                )
            ''')

            # Create smartmoneymovementsbatch table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS smartmoneymovementsbatch (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    walletaddress TEXT NOT NULL UNIQUE,
                    lastfetchedat INTEGER,  -- Store as UNIX timestamp
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def storeMovementsBatch(self, batch_data: List[Tuple], cursor: Optional[sqlite3.Cursor] = None) -> bool:
        """
        Store multiple movement records in a single batch operation
        
        Args:
            batch_data: List of tuples containing movement data
                (wallet_address, token_address, buy_token_change, sell_token_change,
                 buy_usd_change, sell_usd_change, buy_token_name, sell_token_name, date)
            cursor: Optional database cursor for transaction management
            
        Returns:
            bool: Success status
        """
        if not batch_data:
            logger.info("No movements to store")
            return True
            
        try:
            if cursor:
                cursor.executemany('''
                    INSERT INTO smartmoneymovements 
                    (walletaddress, tokenaddress, buytokenchange, selltokenchange,
                     buyusdchange, sellusdchange, buytokenname, selltokenname, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(walletaddress, tokenaddress, date) DO UPDATE SET
                        buytokenchange = buytokenchange + excluded.buytokenchange,
                        selltokenchange = selltokenchange + excluded.selltokenchange,
                        buyusdchange = buyusdchange + excluded.buyusdchange,
                        sellusdchange = sellusdchange + excluded.sellusdchange,
                        buytokenname = CASE WHEN excluded.buytokenname IS NOT NULL THEN excluded.buytokenname ELSE buytokenname END,
                        selltokenname = CASE WHEN excluded.selltokenname IS NOT NULL THEN excluded.selltokenname ELSE selltokenname END
                ''', batch_data)
                logger.info(f"Successfully stored {len(batch_data)} movement records")
                return True
            else:
                with self.conn_manager.transaction() as cur:
                    return self.storeMovementsBatch(batch_data, cur)
        except Exception as e:
            logger.error(f"Failed to store movements batch: {str(e)}")
            return False

    def updateLastFetchedTime(self, wallet_address: str, 
                              cursor: Optional[sqlite3.Cursor] = None) -> bool:
        """
        Update the last fetched time for a wallet's batch processing
        
        Args:
            wallet_address: Wallet address to update
            cursor: Optional database cursor for transaction management
        
        Returns:
            bool: Success status
        """
        try:
            current_time = int(datetime.now().timestamp())
            
            if cursor:
                cursor.execute('''
                    INSERT INTO smartmoneymovementsbatch 
                    (walletaddress, lastfetchedat, updatedat)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(walletaddress) DO UPDATE SET
                        lastfetchedat = excluded.lastfetchedat,
                        updatedat = CURRENT_TIMESTAMP
                ''', (wallet_address, current_time))
                return cursor.rowcount > 0
            else:
                with self.conn_manager.transaction() as cur:
                    return self.updateLastFetchedTime(wallet_address, cur)
        except Exception as e:
            logger.error(f"Failed to update batch fetch time: {str(e)}")
            return False

    def getLastFetchedTime(self, wallet_address: str) -> Optional[int]:
        """
        Get the last fetch time for a wallet's batch processing
        
        Args:
            wallet_address: Wallet address to query
            
        Returns:
            Optional[int]: Last fetch time as UNIX timestamp if found
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT lastfetchedat 
                    FROM smartmoneymovementsbatch
                    WHERE walletaddress = ?
                """, (wallet_address,))
                row = cursor.fetchone()
                return row['lastfetchedat'] if row and row['lastfetchedat'] else None
        except Exception as e:
            logger.error(f"Failed to get last fetch time: {str(e)}")
            return None

    