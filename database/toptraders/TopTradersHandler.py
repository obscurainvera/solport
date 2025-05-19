"""
Handler for managing top traders data in the database
"""
from database.operations.base_handler import BaseSQLiteHandler
from typing import List, Dict, Optional
from datetime import datetime
import pytz
from logs.logger import get_logger

logger = get_logger(__name__)

class TopTradersHandler(BaseSQLiteHandler):
    """Handler for managing top traders data"""
    
    def __init__(self, conn_manager):
        """Initialize the handler with a connection manager"""
        super().__init__(conn_manager)
        self._create_tables()
    
    def _create_tables(self):
        """Create the required tables if they don't exist"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS toptraders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    walletaddress VARCHAR(255) NOT NULL,
                    tokenid VARCHAR(255) NOT NULL,
                    tokenname VARCHAR(255) NOT NULL,
                    chain VARCHAR(50) NOT NULL,
                    pnl DECIMAL(30, 10),
                    roi DECIMAL(30, 10),
                    avgentry DECIMAL(30, 10),
                    avgexit DECIMAL(30, 10),
                    startedat TIMESTAMP,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(walletaddress, tokenid)
                )
            ''')
            
            # Create index for faster lookups
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_toptraders_wallet_token 
                ON toptraders(walletaddress, tokenid)
            ''')
    
    def upsert_trader(self, trader_data: Dict) -> bool:
        """
        Insert or update a trader record
        
        Args:
            trader_data: Dictionary containing trader data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute('''
                    INSERT INTO toptraders (
                        walletaddress, tokenid, tokenname, chain, pnl, roi,
                        avgentry, avgexit, startedat, createdat, updatedat
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(walletaddress, tokenid) DO UPDATE SET
                        tokenname = excluded.tokenname,
                        chain = excluded.chain,
                        pnl = excluded.pnl,
                        roi = excluded.roi,
                        avgentry = excluded.avgentry,
                        avgexit = excluded.avgexit,
                        startedat = excluded.startedat,
                        updatedat = excluded.updatedat
                ''', (
                    trader_data['walletaddress'],
                    trader_data['tokenid'],
                    trader_data['tokenname'],
                    trader_data['chain'],
                    trader_data.get('pnl'),
                    trader_data.get('roi'),
                    trader_data.get('avgentry'),
                    trader_data.get('avgexit'),
                    trader_data.get('startedat'),
                    trader_data.get('createdat'),
                    trader_data.get('updatedat')
                ))
                return True
        except Exception as e:
            logger.error(f"Error upserting trader data: {e}")
            return False
    
    def batchUpsertTraders(self, traders_data: List[Dict]) -> bool:
        """
        Insert or update multiple trader records in a batch
        
        Args:
            traders_data: List of trader data dictionaries
            
        Returns:
            bool: True if all operations were successful, False otherwise
        """
        try:
            # Get current time in IST for any missing timestamps
            ist_timezone = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')
            
            with self.conn_manager.transaction() as cursor:
                for trader in traders_data:
                    # Ensure createdat and updatedat are present
                    if 'createdat' not in trader:
                        trader['createdat'] = current_time
                    if 'updatedat' not in trader:
                        trader['updatedat'] = current_time
                        
                    cursor.execute('''
                        INSERT INTO toptraders (
                            walletaddress, tokenid, tokenname, chain, pnl, roi,
                            avgentry, avgexit, startedat, createdat, updatedat
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(walletaddress, tokenid) DO UPDATE SET
                            tokenname = excluded.tokenname,
                            chain = excluded.chain,
                            pnl = excluded.pnl,
                            roi = excluded.roi,
                            avgentry = excluded.avgentry,
                            avgexit = excluded.avgexit,
                            startedat = excluded.startedat,
                            updatedat = ?
                    ''', (
                        trader['walletaddress'],
                        trader['tokenid'],
                        trader['tokenname'],
                        trader['chain'],
                        trader.get('pnl'),
                        trader.get('roi'),
                        trader.get('avgentry'),
                        trader.get('avgexit'),
                        trader.get('startedat'),
                        trader['createdat'],
                        trader['updatedat'],
                        current_time  # Always update the updatedat timestamp on conflict
                    ))
            return True
        except Exception as e:
            logger.error(f"Error in batch upsert of traders: {e}")
            return False
