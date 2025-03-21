from database.operations.base_handler import BaseSQLiteHandler
from typing import List, Dict, Optional
from decimal import Decimal
import sqlite3
from datetime import datetime, timedelta
from logs.logger import get_logger
from database.operations.schema import AttentionData, AttentionStatusEnum
import pytz

logger = get_logger(__name__)

class AttentionHandler(BaseSQLiteHandler):
    def __init__(self, conn_manager):
        super().__init__(conn_manager)
        self._createTables()
    
    def _createTables(self):
        """Creates all required tables for attention tracking"""
        with self.conn_manager.transaction() as cursor:
            # Registry of all tokens being tracked
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attentiontokenregistry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tokenid VARCHAR(255),
                    name VARCHAR(100),
                    chain VARCHAR(50),
                    firstseenat TIMESTAMP NOT NULL,
                    lastseenat TIMESTAMP NOT NULL,
                    currentstatus VARCHAR(20) DEFAULT 'NEW',
                    attentioncount INT DEFAULT 1,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Raw attention score data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attentiondata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tokenid VARCHAR(255),
                    name VARCHAR(100),
                    chain VARCHAR(50),
                    attentionscore TEXT NOT NULL,
                    change1hbps INTEGER,
                    change1dbps INTEGER,
                    change7dbps INTEGER,
                    change30dbps INTEGER,
                    recordedat TIMESTAMP NOT NULL,
                    datasource VARCHAR(50) NOT NULL,
                    registryid INTEGER,
                    FOREIGN KEY (registryid) REFERENCES attentiontokenregistry(id)
                )
            ''')
            
            # Create history table for attention data
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attentiondatahistory (
                    historyid INTEGER PRIMARY KEY AUTOINCREMENT,
                    attentiondataid INTEGER NOT NULL,
                    tokenid VARCHAR(255),
                    name VARCHAR(100),
                    chain VARCHAR(50),
                    attentionscore TEXT NOT NULL,
                    change1hbps INTEGER,
                    change1dbps INTEGER,
                    change7dbps INTEGER,
                    change30dbps INTEGER,
                    recordedat TIMESTAMP NOT NULL,
                    datasource VARCHAR(50) NOT NULL,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (attentiondataid) REFERENCES attentiondata(id)
                )
            ''')

    def updateTokenRegistry(self, data: AttentionData) -> None:
        """
        Update or create token registry entry
        
        Args:
            data: Attention data to register
        """
        try:
            # Skip if no tokenId is provided
            if not data.tokenid:
                logger.warning(f"Skipping token registry update for token with no ID: {data.name}")
                return None
            
            with self.conn_manager.transaction() as cursor:
                # Get current time for timestamp
                currentTime = self.getCurrentIstTime()
                
                # Check if token exists
                existing = self._getExistingTokenRegistryEntry(cursor, data.tokenid)
                
                if existing:
                    # Check if last seen time is different from current time
                    lastSeenTime = datetime.fromisoformat(existing['lastseenat'])
                    if lastSeenTime.date() != currentTime.date():
                        self._updateExistingTokenRegistryEntry(cursor, data.tokenid, currentTime)
                        logger.info(f"Updated existing token registry entry for {data.tokenid}")
                    return existing['id']
                else:
                    registry_id = self._createNewTokenRegistryEntry(cursor, data, currentTime)
                    logger.info(f"Created new token registry entry for {data.tokenid}")
                    return registry_id
                    
        except Exception as e:
            logger.error(f"Failed to update token registry for {data.tokenid or data.name}: {str(e)}")
            return None

    def _getExistingTokenRegistryEntry(self, cursor, tokenId: str) -> Optional[sqlite3.Row]:
        """
        Check if a token exists in the registry
        
        Args:
            cursor: Database cursor
            tokenId: Token ID to check
            
        Returns:
            Optional[sqlite3.Row]: Existing token entry or None
        """
        if not tokenId:
            return None
        
        return cursor.execute("""
            SELECT id, tokenid, chain, currentstatus, lastseenat 
            FROM attentiontokenregistry 
            WHERE tokenid = ?
        """, (tokenId,)).fetchone()

    def _updateExistingTokenRegistryEntry(self, cursor, tokenId: str, currentTime: datetime) -> None:
        """
        Update an existing token registry entry
        
        Args:
            cursor: Database cursor
            tokenId: Token ID to update
            currentTime: Current timestamp
        """
        if not tokenId:
            return
        
        cursor.execute("""
            UPDATE attentiontokenregistry 
            SET lastseenat = ?,
                attentioncount = attentioncount + 1,
                currentstatus = ?
            WHERE tokenid = ?
        """, (currentTime, AttentionStatusEnum.ACTIVE.value, tokenId))

    def _createNewTokenRegistryEntry(self, cursor, data: AttentionData, currentTime: datetime) -> Optional[int]:
        """
        Create a new token registry entry
        
        Args:
            cursor: Database cursor
            data: Attention data
            currentTime: Current timestamp
            
        Returns:
            Optional[int]: Registry ID if successful, None otherwise
        """
        # Skip if no tokenId is provided
        if not data.tokenid:
            logger.warning(f"Skipping token registry creation for token with no ID: {data.name}")
            return None
        
        cursor.execute("""
            INSERT INTO attentiontokenregistry (
                tokenid, name, chain,
                firstseenat, lastseenat,
                currentstatus
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.tokenid, 
            data.name, 
            data.chain,
            currentTime, 
            currentTime,
            AttentionStatusEnum.NEW.value
        ))
        
        # Get the ID of the newly inserted registry entry
        registry_id = cursor.lastrowid
        return registry_id

    def storeCurrentAttentionData(self, data: AttentionData) -> None:
        """
        Store raw attention data and calculate hourly change
        
        Args:
            data: Attention data to store
        """
        try:
            with self.conn_manager.transaction() as cursor:
                # Step 1: Update or create token registry entry to get registry ID
                registry_id = None
                if data.tokenid:
                    registry_id = self.updateTokenRegistry(data)
                
                # Step 2: Get the last record for this token (for change calculation)
                lastRecord = None
                if data.tokenid:
                    lastRecord = self._getLastAttentionRecord(cursor, data.tokenid)
                
                # Step 3: Calculate hourly change if previous record exists
                change1hbps = self._calculateHourlyChange(lastRecord, data.attentionscore)
                
                # Step 4: If we have a previous record, store it in history
                if lastRecord:
                    self._persistRecordToHistory(cursor, lastRecord)
                    logger.info(f"Stored previous record (ID: {lastRecord['id']}) in history for token {data.tokenid or data.name}")
                    
                    # Step 5a: Update the existing record
                    self._updateExistingRecord(cursor, lastRecord['id'], data, change1hbps, registry_id)
                    logger.info(f"Updated existing record (ID: {lastRecord['id']}) for token {data.tokenid or data.name}")
                else:
                    # Step 5b: Insert a new record if no previous record exists
                    self._insertNewRecord(cursor, data, change1hbps, registry_id)
                    logger.info(f"Inserted new record for token {data.tokenid or data.name}")
                
        except Exception as e:
            logger.error(f"Failed to store attention data for {data.tokenid or data.name}: {str(e)}")
            raise

    def updateInactiveTokens(self) -> None:
        """
        Update status of tokens that haven't been seen for more than 2 days
        """
        try:
            with self.conn_manager.transaction() as cursor:
                currentTime = self.getCurrentIstTime()
                twoDaysAgo = currentTime - timedelta(days=2)
                
                # Update tokens that haven't been seen for more than 2 days
                cursor.execute("""
                    UPDATE attentiontokenregistry 
                    SET currentstatus = ?,
                        attentioncount = 0
                    WHERE lastseenat < ? 
                    AND currentstatus != ?
                """, (
                    AttentionStatusEnum.INACTIVE.value,
                    twoDaysAgo,
                    AttentionStatusEnum.INACTIVE.value
                ))
                
                updatedCount = cursor.rowcount
                logger.info(f"Updated {updatedCount} inactive tokens")
                
        except Exception as e:
            logger.error(f"Failed to update inactive tokens: {str(e)}")
            raise

    def _getLastAttentionRecord(self, cursor, tokenId: str) -> Optional[sqlite3.Row]:
        """
        Get the most recent record for a token
        
        Args:
            cursor: Database cursor
            tokenId: Token ID to look up
            
        Returns:
            Optional[sqlite3.Row]: Most recent record or None
        """
        if not tokenId:
            return None
        
        return cursor.execute("""
            SELECT * 
            FROM attentiondata 
            WHERE tokenid = ? 
            ORDER BY recordedat DESC 
            LIMIT 1
        """, (tokenId,)).fetchone()
    
    def _calculateHourlyChange(self, lastRecord, currentScore: Decimal) -> Optional[int]:
        """Calculate hourly change in basis points"""
        if not lastRecord or not lastRecord['attentionscore']:
            return None
            
        prevScore = Decimal(lastRecord['attentionscore'])
        if prevScore <= 0:  # Avoid division by zero
            return None
            
        return int((currentScore - prevScore) * 10000 / prevScore)
    
    def _persistRecordToHistory(self, cursor, record: sqlite3.Row) -> None:
        """
        Store an existing record in the history table
        
        Args:
            cursor: Database cursor
            record: Record to store in history
        """
        cursor.execute("""
            INSERT INTO attentiondatahistory (
                attentiondataid, tokenid, name, chain,
                attentionscore, change1hbps,
                change1dbps, change7dbps,
                change30dbps, recordedat,
                datasource
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record['id'], 
            record['tokenid'] if record['tokenid'] else None, 
            record['name'] if record['name'] else None,
            record['chain'] if record['chain'] else None,
            record['attentionscore'], 
            record['change1hbps'],
            record['change1dbps'], 
            record['change7dbps'],
            record['change30dbps'], 
            record['recordedat'],
            record['datasource']
        ))
    
    def _updateExistingRecord(self, cursor, recordId: int, data: AttentionData, change1hbps: Optional[int], registry_id: Optional[int] = None) -> None:
        """
        Update an existing record with new data
        
        Args:
            cursor: Database cursor
            recordId: ID of the record to update
            data: Attention data
            change1hbps: Hourly change in basis points
            registry_id: ID of the token registry entry
        """
        cursor.execute("""
            UPDATE attentiondata SET
                attentionscore = ?,
                change1hbps = ?,
                change1dbps = ?,
                change7dbps = ?,
                change30dbps = ?,
                datasource = ?,
                registryid = ?
            WHERE id = ?
        """, (
            str(data.attentionscore), 
            change1hbps,
            data.change1dbps, 
            data.change7dbps,
            data.change30dbps, 
            data.datasource,
            registry_id,
            recordId
        ))
    
    def _insertNewRecord(self, cursor, data: AttentionData, change1hbps: Optional[int], registryId: Optional[int] = None) -> None:
        """
        Insert a new record
        
        Args:
            cursor: Database cursor
            data: Attention data
            change1hbps: Hourly change in basis points
            registry_id: ID of the token registry entry
        """
        cursor.execute("""
            INSERT INTO attentiondata (
                tokenid, name, chain,
                attentionscore, change1hbps,
                change1dbps, change7dbps,
                change30dbps, recordedat,
                datasource, registryid
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.tokenid if data.tokenid else None, 
            data.name if data.name else None, 
            data.chain if data.chain else None,
            str(data.attentionscore), 
            change1hbps,
            data.change1dbps, 
            data.change7dbps,
            data.change30dbps, 
            data.recordedat,
            data.datasource,
            registryId
        ))

    def _storeAttentionDataHistory(self, cursor, attentiondataid: int, data: AttentionData, change1hbps: Optional[int] = None) -> None:
        """Store a record in the attention data history table"""
        try:
            cursor.execute("""
                INSERT INTO attentiondatahistory (
                    attentiondataid, tokenid, name, chain,
                    attentionscore, change1hbps,
                    change1dbps, change7dbps,
                    change30dbps, recordedat,
                    datasource
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (attentiondataid, data.tokenid, data.name, data.chain,
                 str(data.attentionscore), change1hbps,
                 data.change1dbps, data.change7dbps,
                 data.change30dbps, data.recordedat,
                 data.datasource))
            
        except Exception as e:
            logger.error(f"Failed to store history data for {data.tokenid}: {str(e)}")
            # Don't raise here to avoid breaking the main flow
            # Just log the error

    def getConsecutiveRecords(self, cursor, tokenId: str) -> int:
        """Get count of consecutive records above threshold"""
        records = cursor.execute("""
            SELECT attentionscore 
            FROM attentiondata 
            WHERE tokenid = ? 
            AND recordedat >= datetime('now', ? || ' hours')
            ORDER BY recordedat DESC
        """, (tokenId, -24)).fetchall()
        
        return len(records)

    def isReturningToken(self, cursor, tokenId: str, returnDays: int) -> bool:
        """Check if token is returning after inactivity"""
        lastRecord = cursor.execute("""
            SELECT recordedat 
            FROM attentiondata 
            WHERE tokenid = ? 
            AND recordedat < datetime('now')
            ORDER BY recordedat DESC 
            LIMIT 1
        """, (tokenId,)).fetchone()
        
        if not lastRecord:
            return False
            
        # Use base handler's getCurrentIstTime method
        currentTime = self.getCurrentIstTime()
        daysInactive = (currentTime - datetime.fromisoformat(lastRecord['recordedat'])).days
        return daysInactive >= returnDays

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
                # Get the most recent attention data for the token
                cursor.execute("""
                    SELECT * FROM attentiondata
                    WHERE tokenid = ?
                    ORDER BY recordedat DESC
                    LIMIT 1
                """, (tokenId,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                    
                # Get registry data if available
                registryData = {}
                if row['registryid']:
                    cursor.execute("""
                        SELECT * FROM attentiontokenregistry
                        WHERE id = ?
                    """, (row['registryid'],))
                
                    registryRow = cursor.fetchone()
                    if registryRow:
                        registryData = dict(registryRow)
                
                # Combine data
                result = dict(row)
                result.update({
                    'firstseenat': registryData.get('firstseenat'),
                    'lastseenat': registryData.get('lastseenat'),
                    'currentstatus': registryData.get('currentstatus'),
                    'attentioncount': registryData.get('attentioncount')
                })
                
                return result
                
        except Exception as e:
            logger.error(f"Failed to get token data for analysis: {str(e)}")
            return None

