from database.smartmoneywallets.WalletPNLStatusEnum import SmartWalletPnlStatus
from database.operations.base_handler import BaseSQLiteHandler
from typing import Dict, Optional, List
import sqlite3
from datetime import datetime
from logs.logger import get_logger
from database.operations.schema import SmartMoneyWallet

logger = get_logger(__name__)

class SmartMoneyWalletsHandler(BaseSQLiteHandler):
    """
    Handler for smart money wallets data.
    Manages smart money wallets data.
    """
    
    def __init__(self, conn_manager):
        super().__init__(conn_manager)
        self._create_tables()

    def _create_tables(self):
        """Create smartmoneywallets table if it doesn't exist"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS smartmoneywallets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    walletaddress TEXT NOT NULL UNIQUE,
                    profitandloss DECIMAL NOT NULL,
                    tradecount INTEGER NOT NULL,
                    firstseen TIMESTAMP,
                    lastseen TIMESTAMP,
                    createdtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    lastupdatetime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status INTEGER DEFAULT {SmartWalletPnlStatus.LOW_PNL_SM.value}
                )
            ''')

    def insertSmartMoneyWallet(self, wallet: SmartMoneyWallet, cursor: Optional[sqlite3.Cursor] = None) -> Optional[int]:
        """
        Insert new smart money wallet record
        
        Args:
            wallet: SmartMoneyWallet object containing wallet data
            cursor: Optional database cursor for transaction management
        
        Returns:
            Optional[int]: Inserted record ID if successful, None otherwise
        """
        try:
            currentTime = self.getCurrentIstTime()
            wallet.firstSeen = currentTime
            wallet.lastSeen = currentTime
            
            if cursor:
                cursor.execute('''
                    INSERT INTO smartmoneywallets 
                    (walletaddress, profitandloss, tradecount, firstseen, lastseen, 
                     createdtime, lastupdatetime, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    wallet.walletaddress,
                    str(wallet.profitandloss),
                    wallet.tradecount,
                    wallet.firstseen,
                    wallet.lastseen,
                    currentTime,
                    currentTime,
                    wallet.status
                ))
                return cursor.lastrowid
            else:
                with self.conn_manager.transaction() as cur:
                    return self.insertSmartMoneyWallet(wallet, cur)
        except Exception as e:
            logger.error(f"Failed to insert smart money wallet: {str(e)}")
            return None

    def updateSmartMoneyWallet(self, wallet: SmartMoneyWallet, cursor: Optional[sqlite3.Cursor] = None) -> bool:
        """
        Update existing smart money wallet record
        
        Args:
            wallet: SmartMoneyWallet object containing wallet data
            cursor: Optional database cursor for transaction management
        
        Returns:
            bool: Success status
        """
        try:
            currentTime = self.getCurrentIstTime()
            wallet.lastseen = currentTime
            
            if cursor:
                cursor.execute('''
                    UPDATE smartmoneywallets 
                    SET profitandloss = ?,
                        tradecount = ?,
                        lastseen = ?,
                        lastupdatetime = ?,
                        status = ?
                    WHERE walletaddress = ?
                ''', (
                    str(wallet.profitandloss),
                    wallet.tradecount,
                    wallet.lastseen,
                    currentTime,
                    wallet.status,
                    wallet.walletaddress
                ))
                return cursor.rowcount > 0
            else:
                with self.conn_manager.transaction() as cur:
                    return self.updateSmartMoneyWallet(wallet, cur)
        except Exception as e:
            logger.error(f"Failed to update smart money wallet: {str(e)}")
            return False

    def getSmartMoneyWallet(self, wallet_address: str) -> Optional[Dict]:
        """
        Get smart money wallet data for specific wallet
        
        Args:
            wallet_address: Wallet address to query
            
        Returns:
            Optional[Dict]: Smart money wallet data if found
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT * FROM smartmoneywallets
                    WHERE walletaddress = ?
                """, (wallet_address,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get smart money wallet: {str(e)}")
            return None

    def getAllSmartMoneyWallets(self) -> List[Dict]:
        """
        Get all smart money wallets
        
        Returns:
            List[Dict]: List of smart money wallets records
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT * FROM smartmoneywallets
                    ORDER BY 
                        status ASC,
                        CAST(profitandloss AS DECIMAL) DESC
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get smart money wallets: {str(e)}")
            return []

    def getAllHighPnlSmartMoneyWallets(self) -> List[Dict]:
        """
        Get wallets with HIGH_PNL_SM status formatted for front-end
        
        Returns:
            List of dictionaries containing wallet data formatted for front-end
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT 
                        walletaddress,
                        profitandloss,
                        status
                    FROM smartmoneywallets
                    WHERE status = ?
                    ORDER BY CAST(profitandloss AS DECIMAL) DESC
                """, (SmartWalletPnlStatus.HIGH_PNL_SM.value,))
                rows = cursor.fetchall()
                
                wallets = []
                for row in rows:
                    wallet = {
                        "walletAddress": row[0],
                        "walletName": row[0],  # Using address as name
                        "profitAndLoss": row[1],
                        "status": row[2],
                        "statusDescription": SmartWalletPnlStatus.getDescription(row[2])
                    }
                    wallets.append(wallet)
                
                return wallets
        except Exception as e:
            logger.error(f"Failed to get high profit smart money wallets: {str(e)}")
            return [] 