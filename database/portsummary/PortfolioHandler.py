from database.operations.base_handler import BaseSQLiteHandler
from database.operations.schema import PortfolioSummary
from typing import List, Dict, Optional
from decimal import Decimal
import json
import sqlite3
from logs.logger import get_logger
from config.AnalysisStatusEnum import AnalysisStatus
from datetime import datetime, timedelta
import pytz

logger = get_logger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class PortfolioHandler(BaseSQLiteHandler):
    def __init__(self, conn_manager):
        super().__init__(conn_manager)  # Properly initialize base class
        self._create_tables()

    def _create_tables(self):
        with self.conn_manager.transaction() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portsummary (
                    portsummaryid INTEGER PRIMARY KEY AUTOINCREMENT,
                    chainname TEXT NOT NULL,
                    tokenid TEXT NOT NULL,
                    name TEXT NOT NULL,
                    tokenage TEXT NOT NULL,
                    mcap DECIMAL NOT NULL,
                    currentprice DECIMAL NOT NULL,
                    avgprice DECIMAL NOT NULL,
                    smartbalance DECIMAL NOT NULL,
                    walletsinvesting1000 INTEGER NOT NULL,
                    walletsinvesting5000 INTEGER NOT NULL,
                    walletsinvesting10000 INTEGER NOT NULL,
                    qtychange1d DECIMAL NOT NULL,
                    qtychange7d DECIMAL NOT NULL,
                    qtychange30d DECIMAL NOT NULL,
                    status INTEGER DEFAULT 1,
                    firstseen TIMESTAMP NOT NULL,
                    lastseen TIMESTAMP NOT NULL,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT,
                    markedinactive TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portsummaryhistory (
                    historyid INTEGER PRIMARY KEY AUTOINCREMENT,
                    portsummaryid INTEGER NOT NULL,
                    tokenid TEXT NOT NULL,
                    chainname TEXT NOT NULL,
                    name TEXT NOT NULL,
                    tokenage TEXT NOT NULL,
                    mcap DECIMAL NOT NULL,
                    currentprice DECIMAL NOT NULL,
                    avgprice DECIMAL NOT NULL,
                    smartbalance DECIMAL NOT NULL,
                    walletsinvesting1000 INTEGER NOT NULL,
                    walletsinvesting5000 INTEGER NOT NULL,
                    walletsinvesting10000 INTEGER NOT NULL,
                    qtychange1d DECIMAL NOT NULL,
                    qtychange7d DECIMAL NOT NULL,
                    qtychange30d DECIMAL NOT NULL,
                    status INTEGER DEFAULT 1,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT,
                    FOREIGN KEY (portsummaryid) REFERENCES portsummary(portsummaryid)
                )
            ''')

    def insertSummary(self, item: PortfolioSummary, cursor: Optional[sqlite3.Cursor] = None) -> None:
        currentTime = datetime.now()
        
        # Ensure timestamp fields are set
        if not hasattr(item, 'firstseen') or item.firstseen is None:
            item.firstseen = currentTime
        if not hasattr(item, 'lastseen') or item.lastseen is None:
            item.lastseen = currentTime
        if not hasattr(item, 'createdat') or item.createdat is None:
            item.createdat = currentTime
        if not hasattr(item, 'updatedat') or item.updatedat is None:
            item.updatedat = currentTime
        
        query = """
            INSERT INTO portsummary (
                chainname, tokenid, name, tokenage, mcap, currentprice,
                avgprice, smartbalance, walletsinvesting1000,
                walletsinvesting5000, walletsinvesting10000,
                qtychange1d, qtychange7d, qtychange30d, status, tags,
                firstseen, lastseen, createdat, updatedat
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        params = (
            item.chainname, item.tokenid, item.name, item.tokenage,
            str(item.mcap), str(item.currentprice), str(item.avgprice),
            str(item.smartbalance), item.walletsinvesting1000,
            item.walletsinvesting5000, item.walletsinvesting10000,
            str(item.qtychange1d), str(item.qtychange7d),
            str(item.qtychange30d), item.status,
            json.dumps(item.tags) if item.tags else '[]',
            item.firstseen, item.lastseen, item.createdat, item.updatedat
        )

        if cursor:
            cursor.execute(query, params)
        else:
            with self.conn_manager.transaction() as cur:
                cur.execute(query, params)

    def updateSummary(self, item: PortfolioSummary, cursor: Optional[sqlite3.Cursor] = None) -> None:
        currentTime = datetime.now()
        query = """
            UPDATE portsummary SET
                chainname = ?, name = ?, tokenage = ?, mcap = ?,
                currentprice = ?, avgprice = ?, smartbalance = ?,
                walletsinvesting1000 = ?, walletsinvesting5000 = ?,
                walletsinvesting10000 = ?, qtychange1d = ?,
                qtychange7d = ?, qtychange30d = ?, status = ?,
                tags = ?, lastseen = ?, updatedat = ?
            WHERE tokenid = ?
        """
        params = (
            item.chainname, item.name, item.tokenage, str(item.mcap),
            str(item.currentprice), str(item.avgprice), str(item.smartbalance),
            item.walletsinvesting1000, item.walletsinvesting5000,
            item.walletsinvesting10000, str(item.qtychange1d),
            str(item.qtychange7d), str(item.qtychange30d), item.status,
            json.dumps(item.tags) if item.tags else '[]', currentTime, currentTime, item.tokenid
        )

        if cursor:
            cursor.execute(query, params)
        else:
            with self.conn_manager.transaction() as cur:
                cur.execute(query, params)

    def insertHistory(self, item: PortfolioSummary, cursor: Optional[sqlite3.Cursor] = None) -> None:
        current_time = datetime.now()
        query = """
            INSERT INTO portsummaryhistory (
                portsummaryid, tokenid, chainname, name, tokenage,
                mcap, currentprice, avgprice, smartbalance,
                walletsinvesting1000, walletsinvesting5000,
                walletsinvesting10000, qtychange1d, qtychange7d,
                qtychange30d, status, tags, createdat, updatedat
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """
        
        # Ensure createdat is not None
        item_createdat = item.createdat if hasattr(item, 'createdat') and item.createdat is not None else current_time
        
        # Ensure tags are properly serialized as JSON
        if hasattr(item, 'tags'):
            if isinstance(item.tags, list):
                tags_json = json.dumps(item.tags)
            elif isinstance(item.tags, str):
                # If it's already a string, check if it's valid JSON
                try:
                    # Try to parse and re-serialize to ensure valid JSON
                    parsed = json.loads(item.tags)
                    tags_json = json.dumps(parsed)
                except (json.JSONDecodeError, TypeError):
                    # If not valid JSON, treat as comma-separated and convert to JSON
                    tags_list = [tag.strip() for tag in item.tags.split(',') if tag.strip()]
                    tags_json = json.dumps(tags_list)
            else:
                tags_json = '[]'
        else:
            tags_json = '[]'
        
        params = (
            item.portsummaryid, item.tokenid, item.chainname,
            item.name, item.tokenage, str(item.mcap),
            str(item.currentprice), str(item.avgprice),
            str(item.smartbalance), item.walletsinvesting1000,
            item.walletsinvesting5000, item.walletsinvesting10000,
            str(item.qtychange1d), str(item.qtychange7d),
            str(item.qtychange30d), item.status,
            tags_json,
            item_createdat, current_time  # Use safe createdat value
        )

        if cursor:
            cursor.execute(query, params)
        else:
            with self.conn_manager.transaction() as cur:
                cur.execute(query, params)

    def getTokenData(self, token_ids: List[str]) -> List[PortfolioSummary]:
        placeholders = ','.join('?' * len(token_ids))
        query = f"""
            SELECT * FROM portsummary 
            WHERE tokenid IN ({placeholders})
            AND status = ?
        """
        
        with self.conn_manager.transaction() as cursor:
            try:
                # Log the query and parameters for debugging
                logger.debug(f"Executing query: {query}")
                logger.debug(f"Parameters: token_ids={token_ids}, status={AnalysisStatus.ACTIVE.statuscode}")
                
                cursor.execute(query, (*token_ids, AnalysisStatus.ACTIVE.statuscode))
                rows = cursor.fetchall()
                
                # Log the number of rows returned
                logger.debug(f"Found {len(rows)} rows for token_ids {token_ids}")
                
                # If no rows found, let's check if the token exists with any status
                if not rows:
                    cursor.execute(f"""
                        SELECT tokenid, status FROM portsummary 
                        WHERE tokenid IN ({placeholders})
                    """, token_ids)
                    existing_tokens = cursor.fetchall()
                    if existing_tokens:
                        logger.info(f"Tokens found but with different status: {[dict(row) for row in existing_tokens]}")
                
                return [PortfolioSummary(**dict(row)) for row in rows]
                
            except Exception as e:
                logger.error(f"Error in getTokenData: {str(e)}")
                raise

    def getActivePortfolioTokens(self) -> List[Dict]:
        with self.conn_manager.transaction() as cursor:
            cursor.execute("""
                SELECT * FROM portsummary 
                WHERE status = ?
            """, (AnalysisStatus.ACTIVE.statuscode,))
            return [dict(row) for row in cursor.fetchall()]

    def getTokenDataFromPortSummary(self, tokenId: str) -> Optional[Dict]:
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT 
                        portsummaryid,
                        tokenid,
                        status
                    FROM portsummary
                    WHERE tokenid = ?
                    AND status = 1
                """, (tokenId,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Failed to get token portsummary: {str(e)}")
            return None

    def deactivateTokensLostSMBalance(self, cursor: Optional[sqlite3.Cursor] = None) -> int:
        """
        Mark tokens as inactive (status=2) if they haven't been seen for 2+ days
        
        Args:
            cursor: Optional database cursor. If not provided, a new transaction will be created.
            
        Returns:
            int: Number of records marked as inactive
        """
        try:
            # Use provided cursor or create a new transaction
            if cursor is None:
                with self.conn_manager.transaction() as cursor:
                    return self.performDeactivation(cursor)
            else:
                return self.performDeactivation(cursor)
                
        except Exception as e:
            logger.error(f"Failed to deactivate tokens that lost SM balance: {str(e)}")
            raise
            
    def performDeactivation(self, cursor) -> int:
        """
        Internal method to perform the actual deactivation
        
        Args:
            cursor: Database cursor
            
        Returns:
            int: Number of records marked as inactive
        """
        currentTime = datetime.now()
        cutoffDate = (currentTime - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Deactivating tokens not seen since: {cutoffDate}")
        
        # Find tokens to deactivate
        cursor.execute("""
            SELECT portsummaryid, tokenid, name, lastseen
            FROM portsummary 
            WHERE status = 1  -- Active records only
            AND lastseen < ?  -- More than 2 days old
            AND (markedinactive IS NULL OR status != 2)  -- Not already marked inactive
        """, (cutoffDate,))
        
        tokensToDeactivate = cursor.fetchall()
        
        if not tokensToDeactivate:
            logger.info("No tokens found to deactivate")
            return 0
            
        # Log tokens that will be deactivated
        logger.info(f"Found {len(tokensToDeactivate)} tokens to deactivate:")
        tokenIds = []
        
        for token in tokensToDeactivate:
            tokenIds.append(token['portsummaryid'])
            logger.info(f"Will deactivate token: {token['name']} (ID: {token['tokenid']}) "
                      f"Last seen: {token['lastseen']}")
        
        # Update the status of these tokens
        placeholders = ','.join(['?'] * len(tokenIds))
        updateQuery = f"""
            UPDATE portsummary 
            SET 
                status = 2,  -- Set to inactive
                markedinactive = ?,  -- Record when it was marked inactive
                updatedat = ?
            WHERE portsummaryid IN ({placeholders})
        """
        
        cursor.execute(updateQuery, [currentTime, currentTime] + tokenIds)
        affectedRows = cursor.rowcount
        
        logger.info(f"Successfully deactivated {affectedRows} tokens")
        return affectedRows

    def getActiveTokensSince(self, timestamp: datetime) -> List[PortfolioSummary]:
        """Get active tokens since given timestamp"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute("""
                SELECT * FROM portsummary 
                WHERE status = 1 
                AND lastseen >= ?
            """, (timestamp.strftime('%Y-%m-%d %H:%M:%S'),))
            return [PortfolioSummary(**dict(row)) for row in cursor.fetchall()]

    def updateTokenTags(self, cursor: sqlite3.Cursor, tokenId: str, tags: str, timestamp: datetime) -> None:
        """
        Update tags for a token
        
        Args:
            cursor: Database cursor
            tokenId: Token identifier
            tags: Comma-separated tag string
            timestamp: Timestamp for the update
        """
        cursor.execute("""
            UPDATE portsummary 
            SET tags = ?,
                updatedat = ?
            WHERE tokenid = ?
        """, (tags, timestamp, tokenId))

    def get_token_history(self, token_id: str, limit: int = 24) -> List[PortfolioSummary]:
        """
        Get historical records for a token
        
        Args:
            token_id: Token identifier
            limit: Maximum number of records to return
            
        Returns:
            List of historical portfolio summary records
        """
        with self.conn_manager.transaction() as cursor:
            cursor.execute("""
                SELECT * FROM portsummaryhistory 
                WHERE tokenid = ?
                ORDER BY createdat DESC
                LIMIT ?
            """, (token_id, limit))
            return [PortfolioSummary(**dict(row)) for row in cursor.fetchall()]

    def getTokenDataForAnalysis(self, tokenId: str) -> Optional[Dict]:
        """
        Get comprehensive token data for analytics framework
        
        Args:
            tokenId: Token identifier
            
        Returns:
            Dict containing token data or None if not found
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute("""
                    SELECT * FROM portsummary
                    WHERE tokenid = ?
                    AND status = 1
                """, (tokenId,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                return dict(row)
                
        except Exception as e:
            logger.error(f"Failed to get token data for analysis: {str(e)}")
            return None 