from database.operations.base_handler import BaseSQLiteHandler
from database.operations.schema import WalletsInvested
from typing import List, Dict, Optional
from decimal import Decimal, InvalidOperation
import sqlite3
import json
from datetime import datetime
from logs.logger import get_logger
import pytz

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
                    FOREIGN KEY (portsummaryid) REFERENCES portsummary(portsummaryid),
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
                    FOREIGN KEY (walletinvestedid) REFERENCES walletsinvested(walletinvestedid)
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
                    updatedat = ?
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
        """Get wallets with high smart money holdings"""
        try:
            with self.conn_manager.transaction() as cursor:
                if tokenId:
                    cursor.execute("""
                        SELECT walletinvestedid, walletaddress, tokenid, smartholding
                        FROM walletsinvested
                        WHERE smartholding >= ?
                        AND tokenid = ?
                        AND status = 1
                        ORDER BY smartholding DESC
                    """, (str(minBalance), tokenId))
                else:
                    cursor.execute("""
                        SELECT walletinvestedid, walletaddress, tokenid, smartholding
                        FROM walletsinvested
                        WHERE smartholding >= ?
                        AND status = 1
                        ORDER BY smartholding DESC
                    """, (str(minBalance),))
                
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
                    AND status = 1
                """, (walletInvestedId,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            logger.error(f"Failed to get wallet details by ID: {str(e)}")
            return None