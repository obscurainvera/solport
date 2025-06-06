from database.operations.base_handler import BaseSQLiteHandler
from database.operations.schema import WalletsInvested, WalletInvestedStatusEnum
from typing import List, Dict, Optional
from decimal import Decimal, InvalidOperation
import sqlite3
import json
from datetime import datetime
from logs.logger import get_logger
import pytz
from utils.constants import EXCLUDE_TOKEN_IDS

logger = get_logger(__name__)

class WalletsInvestedHandler(BaseSQLiteHandler):
    def __init__(self, conn_manager):
        super().__init__(conn_manager)  # Properly initialize base class
        self._create_tables()

    @staticmethod
    def get_current_ist_time() -> datetime:
        """Get current time in IST timezone"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist)

    def get_current_ist_time(self) -> datetime:
        """Get current time in IST timezone"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist)

    def _create_tables(self):
        with self.conn_manager.transaction() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS walletsinvested (
                    walletinvestedid INTEGER PRIMARY KEY AUTOINCREMENT,
                    portsummaryid INTEGER NOT NULL,
                    tokenid TEXT NOT NULL,
                    walletaddress TEXT NOT NULL,
                    walletname TEXT,
                    coinquantity DECIMAL,
                    smartholding DECIMAL,
                    firstbuytime TIMESTAMP,
                    totalinvestedamount DECIMAL,
                    amounttakenout DECIMAL,
                    totalcoins DECIMAL,
                    avgentry DECIMAL,
                    qtychange1d DECIMAL,
                    qtychange7d DECIMAL,
                    chainedgepnl DECIMAL,
                    transactionscount INTEGER DEFAULT 0,
                    tags TEXT,
                    firstseen TIMESTAMP,
                    lastseen TIMESTAMP,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status INTEGER DEFAULT 1,
                    FOREIGN KEY (portsummaryid) REFERENCES portsummary(portsummaryid) ON DELETE CASCADE,
                    UNIQUE(tokenid, walletaddress)
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS walletsinvestedhistory (
                    historyid INTEGER PRIMARY KEY AUTOINCREMENT,
                    walletinvestedid INTEGER NOT NULL,
                    portsummaryid INTEGER NOT NULL,
                    tokenid TEXT NOT NULL,
                    walletaddress TEXT NOT NULL,
                    walletname TEXT,
                    coinquantity DECIMAL,
                    smartholding DECIMAL,
                    firstbuytime TIMESTAMP,
                    totalinvestedamount DECIMAL,
                    amounttakenout DECIMAL,
                    totalcoins DECIMAL,
                    avgentry DECIMAL,
                    qtychange1d DECIMAL,
                    qtychange7d DECIMAL,
                    chainedgepnl DECIMAL,
                    transactionscount INTEGER,
                    tags TEXT,
                    status INTEGER,
                    snaptimeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    createdat TIMESTAMP NOT NULL,
                    FOREIGN KEY (walletinvestedid) REFERENCES walletsinvested(walletinvestedid) ON DELETE CASCADE,
                    FOREIGN KEY (portsummaryid) REFERENCES portsummary(portsummaryid) ON DELETE CASCADE
                )
            ''')

    def insertWalletInvested(self, wallet: WalletsInvested, cursor: Optional[sqlite3.Cursor] = None) -> Optional[int]:
        """Insert new wallet investment record"""
        try:
            currentTime = self.get_current_ist_time()
            
            query = """
                INSERT INTO walletsinvested (
                    portsummaryid, tokenid, walletaddress, walletname,
                    coinquantity, smartholding, firstbuytime,
                    totalinvestedamount, amounttakenout, totalcoins,
                    avgentry, qtychange1d, qtychange7d, chainedgepnl,
                    tags, firstseen, lastseen, createdat, updatedat, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                wallet.portsummaryid,
                wallet.tokenid,
                wallet.walletaddress,
                wallet.walletname,
                str(wallet.coinquantity),
                str(wallet.smartholding),
                wallet.firstbuytime,
                str(wallet.totalinvestedamount) if wallet.totalinvestedamount else None,
                str(wallet.amounttakenout) if wallet.amounttakenout else None,
                str(wallet.totalcoins) if wallet.totalcoins else None,
                str(wallet.avgentry) if wallet.avgentry else None,
                str(wallet.qtychange1d) if wallet.qtychange1d else None,
                str(wallet.qtychange7d) if wallet.qtychange7d else None,
                str(wallet.chainedgepnl) if wallet.chainedgepnl else None,
                wallet.tags,
                currentTime,
                currentTime,
                currentTime,
                currentTime,
                wallet.status
            )
            
            if cursor:
                cursor.execute(query, params)
                return cursor.lastrowid
            else:
                with self.conn_manager.transaction() as cur:
                    cur.execute(query, params)
                    return cur.lastrowid
                    
        except Exception as e:
            logger.error(f"Failed to insert wallet investment: {str(e)}")
            return None

    def updateWalletsInvested(self, wallet: WalletsInvested, cursor: Optional[sqlite3.Cursor] = None) -> bool:
        """Update existing wallet investment record"""
        try:
            currentTime = self.get_current_ist_time()
            
            query = """
                UPDATE walletsinvested SET
                    coinquantity = ?,
                    smartholding = ?,
                    qtychange1d = ?,
                    qtychange7d = ?,
                    chainedgepnl = ?,
                    lastseen = ?,
                    updatedat = ?,
                    status = ?
                WHERE tokenid = ? AND walletaddress = ?
            """
            
            params = (
                str(wallet.coinquantity),
                str(wallet.smartholding),
                str(wallet.qtychange1d) if wallet.qtychange1d else None,
                str(wallet.qtychange7d) if wallet.qtychange7d else None,
                str(wallet.chainedgepnl) if wallet.chainedgepnl else None,
                currentTime,
                currentTime,
                wallet.status,
                wallet.tokenid,
                wallet.walletaddress
            )
            
            # Log the SQL query and parameters for debugging
            logger.debug(f"Executing SQL: {query}")
            logger.debug(f"With parameters: {params}")
            
            if cursor:
                cursor.execute(query, params)
                rowsAffected = cursor.rowcount
                if rowsAffected == 0:
                    logger.warning(f"No rows affected when updating wallet {wallet.walletaddress} for token {wallet.tokenid}")
                return rowsAffected > 0
            else:
                with self.conn_manager.transaction() as cur:
                    cur.execute(query, params)
                    rowsAffected = cur.rowcount
                    if rowsAffected == 0:
                        logger.warning(f"No rows affected when updating wallet {wallet.walletaddress} for token {wallet.tokenid}")
                    return rowsAffected > 0
                    
        except Exception as e:
            logger.error(f"Failed to update wallet investment for wallet {wallet.walletaddress} and token {wallet.tokenid}: {str(e)}")
            return False

    def insertWalletHistory(self, wallet: Dict, cursor: Optional[sqlite3.Cursor] = None) -> Optional[int]:
        """Insert wallet investment history record"""
        try:
            currentTime = self.get_current_ist_time()
            
            query = """
                INSERT INTO walletsinvestedhistory (
                    walletinvestedid, portsummaryid, tokenid, walletaddress,
                    walletname, coinquantity, smartholding, firstbuytime,
                    totalinvestedamount, amounttakenout, totalcoins,
                    avgentry, qtychange1d, qtychange7d, chainedgepnl,
                    transactionscount, tags, status, createdat
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                wallet['walletinvestedid'],
                wallet['portsummaryid'],
                wallet['tokenid'],
                wallet['walletaddress'],
                wallet['walletname'],
                wallet['coinquantity'],
                wallet['smartholding'],
                wallet['firstbuytime'],
                wallet['totalinvestedamount'],
                wallet['amounttakenout'],
                wallet['totalcoins'],
                wallet['avgentry'],
                wallet['qtychange1d'],
                wallet['qtychange7d'],
                wallet['chainedgepnl'],
                wallet['transactionscount'] if 'transactionscount' in wallet else None,
                wallet['tags'],
                wallet['status'],
                currentTime  # Use current time for createdat
            )
            
            if cursor:
                cursor.execute(query, params)
                return cursor.lastrowid
            else:
                with self.conn_manager.transaction() as cur:
                    cur.execute(query, params)
                    return cur.lastrowid
                    
        except Exception as e:
            logger.error(f"Failed to insert wallet history: {str(e)}")
            return None

    def getWalletInvestedId(self, tokenId: str, walletAddress: str) -> Optional[int]:
        """Get analysis ID for a specific wallet and token"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT walletinvestedid 
                    FROM walletsinvested 
                    WHERE tokenid = ? AND walletaddress = ?
                    AND status = 1
                """, (tokenId, walletAddress))
                
                result = cursor.fetchone()
                return result['walletinvestedid'] if result else None
                
        except Exception as e:
            logger.error(f"Failed to get wallet analysis ID: {str(e)}")
            return None

    def updateWalletInvestmentData(self, walletInvestedId: int, totalInvested: Decimal, 
                                 amountTakenOut: Decimal, avgEntry: Decimal,
                                 totalCoins: Decimal) -> bool:
        """Update investment data for a wallet"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    UPDATE walletsinvested 
                    SET totalinvestedamount = ?,
                        amounttakenout = ?,
                        avgentry = ?,
                        totalcoins = ?,
                        updatedat = ?
                    WHERE walletinvestedid = ?
                """, (
                    str(totalInvested),
                    str(amountTakenOut),
                    str(avgEntry),
                    str(totalCoins),
                    self.get_current_ist_time(),
                    walletInvestedId
                ))
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update wallet investment data: {str(e)}")
            return False

    def getTransactionsCountFromDB(self, walletsInvestedId: int) -> Optional[int]:
        """Get transaction count from database"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT transactionscount 
                    FROM walletsinvested 
                    WHERE walletinvestedid = ?
                """, (walletsInvestedId,))
                
                result = cursor.fetchone()
                return result['transactionscount'] if result else None
                
        except Exception as e:
            logger.error(f"Failed to get transaction count: {str(e)}")
            return None

    def updateTransactionsCountInDB(self, walletInvestedId: int, count: int) -> bool:
        """Update transaction count in database"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    UPDATE walletsinvested 
                    SET transactionscount = ?,
                        updatedat = ?
                    WHERE walletinvestedid = ?
                """, (count, self.get_current_ist_time(), walletInvestedId))
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update transaction count: {str(e)}")
            return False

    def getWalletsWithHighSMTokenHoldings(self, minBalance: Decimal, tokenId: Optional[str] = None) -> List[Dict]:
        """
        Get wallets with high smart money holdings joined with portfolio summary data,
        excluding specific tokens defined in EXCLUDE_TOKEN_IDS
        
        Args:
            minBalance: Minimum balance threshold
            tokenId: Optional specific token ID to filter
            
        Returns:
            List[Dict]: List of wallet records with token details
        """
        try:
            with self.conn_manager.transaction() as cursor:
                # Create placeholders for excluded tokens
                exclude_placeholders = ','.join(['?' for _ in EXCLUDE_TOKEN_IDS])
                
                if tokenId:
                    cursor.execute(f"""
                        SELECT 
                            w.walletinvestedid,
                            w.walletaddress,
                            w.tokenid,
                            w.smartholding,
                            p.name as tokenname
                        FROM walletsinvested w
                        INNER JOIN portsummary p ON w.tokenid = p.tokenid
                        WHERE w.smartholding >= ?
                        AND w.tokenid = ?
                        AND w.status = ?
                        AND w.tokenid NOT IN ({exclude_placeholders})
                        ORDER BY w.smartholding DESC
                    """, (str(minBalance), tokenId, WalletInvestedStatusEnum.ACTIVE, *EXCLUDE_TOKEN_IDS))
                else:
                    cursor.execute(f"""
                        SELECT 
                            w.walletinvestedid,
                            w.walletaddress,
                            w.tokenid,
                            w.smartholding,
                            p.name as tokenname
                        FROM walletsinvested w
                        INNER JOIN portsummary p ON w.tokenid = p.tokenid
                        WHERE w.smartholding >= ?
                        AND w.status = ?
                        AND w.tokenid NOT IN ({exclude_placeholders})
                        ORDER BY w.smartholding DESC
                    """, (str(minBalance), WalletInvestedStatusEnum.ACTIVE, *EXCLUDE_TOKEN_IDS))
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Failed to get wallets with high holdings: {str(e)}")
            return []

    def _to_decimal_str(self, value) -> Optional[str]:
        """
        Convert a value to a decimal string representation
        Args:
            value: The value to convert
        Returns:
            Optional[str]: String representation of decimal or None if value is None/invalid
        """
        try:
            if value is None:
                return None
            return str(Decimal(str(value)))
        except (TypeError, ValueError, InvalidOperation):
            return None

    def getWalletInvestedById(self, walletInvestedId: int) -> Optional[Dict]:
        """Get wallet invested details by ID"""
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT * 
                    FROM walletsinvested 
                    WHERE walletinvestedid = ?
                    AND status = ?
                """, (walletInvestedId, WalletInvestedStatusEnum.ACTIVE))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Failed to get wallet details by ID: {str(e)}")
            return None

    def getActiveWalletsByTokenId(self, tokenId: str) -> List[str]:
        """
        Get all active wallet addresses for a specific token
        
        Args:
            tokenId: The token ID to query
            
        Returns:
            List of active wallet addresses
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT walletaddress FROM walletsinvested 
                    WHERE tokenid = ? AND status = ?
                """, (tokenId, WalletInvestedStatusEnum.ACTIVE))
                
                results = cursor.fetchall()
                return [row['walletaddress'] for row in results] if results else []
        except Exception as e:
            logger.error(f"Failed to get active wallets for token {tokenId}: {str(e)}")
            return []

    def markWalletsAsInactive(self, tokenId: str, walletAddresses: List[str]) -> bool:
        """
        Mark wallets as inactive
        
        Args:
            tokenId: The token ID
            walletAddresses: List of wallet addresses to mark as inactive
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not walletAddresses:
            return True
            
        try:
            currentTime = self.get_current_ist_time()
            with self.conn_manager.transaction() as cursor:
                # First, get all records at once for history
                placeholders = ','.join(['?' for _ in walletAddresses])
                query = f"""
                    SELECT * FROM walletsinvested 
                    WHERE tokenid = ? AND walletaddress IN ({placeholders})
                    AND status = ?
                """
                params = [tokenId] + walletAddresses + [WalletInvestedStatusEnum.ACTIVE]
                
                cursor.execute(query, params)
                existing_records = cursor.fetchall()
                
                # Add all records to history before updating
                for record in existing_records:
                    self.insertWalletHistory(record, cursor)
                
                # Do a bulk update of all wallets at once
                addresses_found = [record['walletaddress'] for record in existing_records]
                if addresses_found:
                    placeholders = ','.join(['?' for _ in addresses_found])
                    update_query = f"""
                        UPDATE walletsinvested 
                        SET status = ?, updatedat = ?
                        WHERE tokenid = ? AND walletaddress IN ({placeholders})
                    """
                    update_params = [WalletInvestedStatusEnum.INACTIVE, currentTime, tokenId] + addresses_found
                    
                    cursor.execute(update_query, update_params)
                    logger.info(f"Marked {len(addresses_found)} wallets as inactive for token {tokenId} and recorded history")
                
                # Log any addresses not found
                addresses_not_found = set(walletAddresses) - set(addresses_found)
                if addresses_not_found:
                    logger.warning(f"{len(addresses_not_found)} wallets not found for token {tokenId}: {', '.join(list(addresses_not_found)[:5])}{'...' if len(addresses_not_found) > 5 else ''}")
                    
            return True
        except Exception as e:
            logger.error(f"Failed to mark wallets as inactive: {str(e)}")
            return False
            
    def getWalletsInvestedByTokenId(self, tokenId: str) -> List[Dict]:
        """
        Get all wallets invested in a specific token
        
        Args:
            tokenId: The token ID to query
            
        Returns:
            List of wallet records
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT * FROM walletsinvested 
                    WHERE tokenid = ?
                """, (tokenId,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []
        except Exception as e:
            logger.error(f"Failed to get wallets for token {tokenId}: {str(e)}")
            return []