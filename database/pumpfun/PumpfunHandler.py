from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime
import json
from database.operations.base_handler import BaseSQLiteHandler
from database.operations.schema import PumpFunToken
from logs.logger import get_logger

logger = get_logger(__name__)

# Table Schema Documentation
SCHEMA_DOCS = {
    "pumpfuninfo": {
        "id": "Internal unique ID",
        "tokenid": "Token's contract address",
        "name": "Trading symbol (e.g., 'SALTY')",
        "tokenname": "Full name (e.g., 'SALTY')",
        "chain": "Blockchain (e.g., 'SOL')",
        "tokendecimals": "Token decimal places",
        "circulatingsupply": "Available supply",
        "tokenage": "Time since launch",
        "twitterlink": "Social media link",
        "telegramlink": "Community chat link",
        "websitelink": "Project website",
        "firstseenat": "When bot first detected",
        "lastupdatedat": "Last data update",
        "count": "Count of updates"
    },

    "pumpfunstates": {
        "id": "Internal unique ID",
        "tokenid": "Reference to pumpfuninfo.tokenid",
        "price": "Current token price in USD",
        "marketcap": "Total market capitalization",
        "liquidity": "Available trading liquidity",
        "volume24h": "24-hour trading volume",
        "buysolqty": "Number of SOL buy transactions",
        "occurrencecount": "Number of times token detected",
        "percentilerankpeats": "Ranking based on occurrences (0-1)",
        "percentileranksol": "Ranking based on SOL buys (0-1)",
        "dexstatus": "Trading status (true=active, false=inactive)",
        "change1hpct": "1-hour price change percentage",
        "createdat": "When record was created",
        "lastupdatedat": "Last state update timestamp"
    },

    "pumpfunhistory": {
        "id": "Internal unique ID",
        "tokenid": "Reference to pumpfuninfo.tokenid",
        "snapshotat": "When this snapshot was taken",
        "price": "Token price at snapshot",
        "marketcap": "Market cap at snapshot",
        "liquidity": "Liquidity at snapshot",
        "volume24h": "24h volume at snapshot",
        "buysolqty": "SOL buys at snapshot",
        "occurrencecount": "Occurrences at snapshot",
        "percentilerankpeats": "Occurrence ranking at snapshot",
        "percentileranksol": "SOL buys ranking at snapshot",
        "dexstatus": "Trading status at snapshot",
        "change1hpct": "1h price change at snapshot",
        "createdat": "When record was created"
    }
}

class PumpFunHandler(BaseSQLiteHandler):
    def __init__(self, conn_manager):
        super().__init__(conn_manager)
        self.schema = SCHEMA_DOCS
        self._createTables()
        
    def _createTables(self):
        """Creates all necessary tables for the system"""
        with self.conn_manager.transaction() as cursor:
            # 1. Base Token Information
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pumpfuninfo (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tokenid TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    tokenname TEXT NOT NULL,
                    chain TEXT NOT NULL,
                    tokendecimals INTEGER NOT NULL,
                    circulatingsupply TEXT,
                    tokenage TEXT,
                    twitterlink TEXT,
                    telegramlink TEXT,
                    websitelink TEXT,
                    firstseenat TIMESTAMP NOT NULL,
                    lastupdatedat TIMESTAMP,
                    count INTEGER DEFAULT 1,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 2. Token Current State
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pumpfunstates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tokenid TEXT NOT NULL UNIQUE,
                    price DECIMAL NOT NULL,
                    marketcap DECIMAL NOT NULL,
                    liquidity DECIMAL NOT NULL,
                    volume24h DECIMAL NOT NULL,
                    buysolqty INTEGER NOT NULL,
                    occurrencecount INTEGER NOT NULL,
                    percentilerankpeats DECIMAL,
                    percentileranksol DECIMAL,
                    dexstatus BOOLEAN NOT NULL,
                    change1hpct DECIMAL NOT NULL,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    lastupdatedat TIMESTAMP,
                    FOREIGN KEY(tokenid) REFERENCES pumpfuninfo(tokenid)
                )
            ''')

            # 3. Token History
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pumpfunhistory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tokenid TEXT NOT NULL,
                    snapshotat TIMESTAMP NOT NULL,
                    price DECIMAL NOT NULL,
                    marketcap DECIMAL NOT NULL,
                    liquidity DECIMAL NOT NULL,
                    volume24h DECIMAL NOT NULL,
                    buysolqty INTEGER NOT NULL,
                    occurrencecount INTEGER NOT NULL,
                    percentilerankpeats DECIMAL,
                    percentileranksol DECIMAL,
                    dexstatus BOOLEAN NOT NULL,
                    change1hpct DECIMAL NOT NULL,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(tokenid) REFERENCES pumpfuninfo(tokenid)
                )
            ''')

            # Create indices for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pumpfuninfo_tokenid ON pumpfuninfo(tokenid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pumpfunstates_tokenid ON pumpfunstates(tokenid)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_pumpfunhistory_tokenid ON pumpfunhistory(tokenid)')

    def insertTokenData(self, token: PumpFunToken) -> None:
        """
        Insert or update token data:
        1. New token: Add to info and state tables
        2. Existing token: Archive current state, update state, increment count
        
        Args:
            token: PumpFunToken object to persist
        """
        try:
            with self.conn_manager.transaction() as cursor:
                self._handleTokenData(cursor, token)
        except Exception as e:
            logger.error(f"Failed to process token {token.tokenid}: {str(e)}")
            raise

    def _handleTokenData(self, cursor, token: PumpFunToken) -> None:
        """Handle token data insertion or update"""
        # Check token existence and get current state in one query
        cursor.execute('''
            SELECT 
                i.id as info_exists,
                s.id as state_exists,
                s.*
            FROM pumpfuninfo i
            LEFT JOIN pumpfunstates s ON i.tokenid = s.tokenid
            WHERE i.tokenid = ?
        ''', (token.tokenid,))
        
        result = cursor.fetchone()
        
        if not result:
            # New token - insert both records
            self._insertNewRecords(cursor, token)
        else:
            # Existing token - archive and update
            if not result['state_exists']:
                logger.error(f"Inconsistent state: Token {token.tokenid} exists in info but not in state table")
                return
            
            self._updateExistingRecords(cursor, token, result)

    def _insertNewRecords(self, cursor, token: PumpFunToken) -> None:
        """Insert new token records in both tables"""
        currentTime = datetime.now()
        
        # Insert info record
        cursor.execute('''
            INSERT INTO pumpfuninfo (
                tokenid, name, tokenname, chain, tokendecimals,
                circulatingsupply, tokenage, twitterlink, telegramlink,
                websitelink, firstseenat, lastupdatedat, count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        ''', (
            token.tokenid, token.name, token.tokenname, token.chain,
            token.tokendecimals, token.circulatingsupply, token.tokenage,
            token.twitterlink, token.telegramlink, token.websitelink,
            currentTime, currentTime
        ))
        
        # Insert state record
        cursor.execute('''
            INSERT INTO pumpfunstates (
                tokenid, price, marketcap, liquidity, volume24h,
                buysolqty, occurrencecount, percentilerankpeats,
                percentileranksol, dexstatus, change1hpct,
                createdat, lastupdatedat
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            token.tokenid, str(token.price), str(token.marketcap),
            str(token.liquidity), str(token.volume24h), token.buysolqty,
            token.occurrencecount, token.percentilerankpeats,
            token.percentileranksol, token.dexstatus,
            str(token.change1hpct), currentTime, currentTime
        ))
        
        logger.info(f"Inserted new token {token.tokenid}")

    def _updateExistingRecords(self, cursor, token: PumpFunToken, currentState: Dict) -> None:
        """
        Archive current state and update records only if key metrics have changed
        
        Key metrics monitored for changes:
        - buysolqty: Number of SOL buy transactions
        - occurrencecount: Number of times token detected
        - percentilerankpeats: Ranking based on occurrences
        - percentileranksol: Ranking based on SOL buys
        """
        # Check if any key metrics have changed
        shouldUpdate = False
        metricsToCompare = [
            ('buysolqty', token.buysolqty, currentState['buysolqty']),
            ('occurrencecount', token.occurrencecount, currentState['occurrencecount']),
            ('percentilerankpeats', token.percentilerankpeats, currentState['percentilerankpeats']),
            ('percentileranksol', token.percentileranksol, currentState['percentileranksol'])
        ]
        
        # Compare metrics and log changes
        changedMetrics = []
        for metricName, newValue, oldValue in metricsToCompare:
            if newValue != oldValue:
                shouldUpdate = True
                changedMetrics.append(f"{metricName}: {oldValue} -> {newValue}")
        
        if not shouldUpdate:
            logger.info(f"No changes detected for token {token.tokenid}, skipping update")
            return
            
        logger.info(f"Changes detected for token {token.tokenid}: {', '.join(changedMetrics)}")
        currentTime = datetime.now()
        
        # 1. Archive current state since we're going to update
        cursor.execute('''
            INSERT INTO pumpfunhistory (
                tokenid, snapshotat, price, marketcap, liquidity,
                volume24h, buysolqty, occurrencecount, percentilerankpeats,
                percentileranksol, dexstatus, change1hpct, createdat
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            currentState['tokenid'], currentState['lastupdatedat'],
            currentState['price'], currentState['marketcap'],
            currentState['liquidity'], currentState['volume24h'],
            currentState['buysolqty'], currentState['occurrencecount'],
            currentState['percentilerankpeats'], currentState['percentileranksol'],
            currentState['dexstatus'], currentState['change1hpct'], currentTime
        ))
        
        # 2. Update state table
        cursor.execute('''
            UPDATE pumpfunstates SET
                price = ?,
                marketcap = ?,
                liquidity = ?,
                volume24h = ?,
                buysolqty = ?,
                occurrencecount = ?,
                percentilerankpeats = ?,
                percentileranksol = ?,
                dexstatus = ?,
                change1hpct = ?,
                lastupdatedat = ?
            WHERE tokenid = ?
        ''', (
            str(token.price), str(token.marketcap), str(token.liquidity),
            str(token.volume24h), token.buysolqty, token.occurrencecount,
            token.percentilerankpeats, token.percentileranksol,
            token.dexstatus, str(token.change1hpct), currentTime,
            token.tokenid
        ))
        
        # 3. Update info table
        cursor.execute('''
            UPDATE pumpfuninfo SET
                count = count + 1,
                lastupdatedat = ?
            WHERE tokenid = ?
        ''', (currentTime, token.tokenid))
        
        logger.info(f"Updated token {token.tokenid} and archived previous state")

    def getTokenHistory(self, tokenId: str, startTime: datetime, endTime: datetime) -> List[Dict]:
        """Get token history for backtesting"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('''
                SELECT * FROM pumpfunhistory 
                WHERE tokenid = ? AND snapshotat BETWEEN ? AND ?
                ORDER BY snapshotat ASC
            ''', (tokenId, startTime, endTime))
            return cursor.fetchall()

    def getTokenInfo(self, tokenId: str) -> Optional[Dict]:
        """Get token basic information"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('SELECT * FROM pumpfuninfo WHERE tokenid = ?', (tokenId,))
            return cursor.fetchone()

    def getTokenState(self, tokenId: str) -> Optional[Dict]:
        """Get token current state"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('SELECT * FROM pumpfunstates WHERE tokenid = ?', (tokenId,))
            return cursor.fetchone()

    def getExistingTokenState(self, tokenId: str) -> Optional[Dict]:
        """Get existing token state for history tracking"""
        with self.conn_manager.transaction() as cursor:
            cursor.execute('''
                SELECT s.*, i.firstseenat
                FROM pumpfunstates s
                JOIN pumpfuninfo i ON s.tokenid = i.tokenid
                WHERE s.tokenid = ?
            ''', (tokenId,))
            return cursor.fetchone() 