from database.operations.base_handler import BaseSQLiteHandler
from typing import List, Dict, Optional, Any
from logs.logger import get_logger
import json

logger = get_logger(__name__)

class AttentionReportHandler(BaseSQLiteHandler):
    """
    Handler for attention report operations.
    Provides methods to query and filter attention data for reporting.
    """
    
    def __init__(self, conn_manager):
        """
        Initialize the handler with a connection manager.
        
        Args:
            conn_manager: Database connection manager instance
        """
        super().__init__(conn_manager)
    
    def getAttentionReport(self,
                         tokenId: str = None,
                         name: str = None,
                         chain: str = None,
                         currentStatus: str = None,
                         minAttentionCount: int = None,
                         maxAttentionCount: int = None,
                         sortBy: str = "attentioncount",
                         sortOrder: str = "desc") -> List[Dict[str, Any]]:
        """
        Get attention report data with optional filters.
        
        Args:
            tokenId: Filter by token ID (partial match)
            name: Filter by token name (partial match)
            chain: Filter by chain name (partial match)
            currentStatus: Filter by current status (exact match)
            minAttentionCount: Minimum attention count filter
            maxAttentionCount: Maximum attention count filter
            sortBy: Field to sort by (default: attentioncount)
            sortOrder: Sort order (asc or desc, default: desc)
            
        Returns:
            List of attention data dictionaries
        """
        # Build the base query - join with attentiondata to get the latest attention score
        query = """
            SELECT 
                r.id,
                r.tokenid,
                r.name,
                r.chain,
                r.currentstatus,
                r.attentioncount,
                a.attentionscore,
                r.firstseenat,
                r.lastseenat
            FROM attentiontokenregistry r
            LEFT JOIN (
                SELECT tokenid, attentionscore
                FROM attentiondata
                WHERE (tokenid, recordedat) IN (
                    SELECT tokenid, MAX(recordedat)
                    FROM attentiondata
                    GROUP BY tokenid
                )
            ) a ON r.tokenid = a.tokenid
            WHERE 1=1
        """
        params = []

        # Add filters based on parameters
        if tokenId:
            query += " AND r.tokenid LIKE ?"
            params.append(f"%{tokenId}%")
        
        if name:
            query += " AND r.name LIKE ?"
            params.append(f"%{name}%")
        
        if chain:
            query += " AND r.chain LIKE ?"
            params.append(f"%{chain}%")
        
        if currentStatus:
            query += " AND r.currentstatus = ?"
            params.append(currentStatus)
        
        if minAttentionCount is not None:
            query += " AND r.attentioncount >= ?"
            params.append(minAttentionCount)
        
        if maxAttentionCount is not None:
            query += " AND r.attentioncount <= ?"
            params.append(maxAttentionCount)
            
        # Validate sort parameters
        valid_sort_fields = ["id", "tokenid", "name", "chain", "currentstatus", "attentioncount", "attentionscore", "firstseenat", "lastseenat"]
        valid_sort_orders = ["asc", "desc"]
        
        if sortBy not in valid_sort_fields:
            sortBy = "attentioncount"
        
        if sortOrder.lower() not in valid_sort_orders:
            sortOrder = "desc"
            
        # Add sorting
        query += f" ORDER BY r.{sortBy} {sortOrder.upper()}"

        # Execute query
        with self.transaction() as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()

            # Convert results to list of dictionaries
            attentionData = []
            for row in results:
                attentionData.append({
                    'id': row[0],
                    'tokenId': row[1],
                    'name': row[2],
                    'chain': row[3],
                    'currentStatus': row[4],
                    'attentionCount': row[5],
                    'attentionScore': float(row[6]) if row[6] else None,
                    'firstSeenAt': row[7],
                    'lastSeenAt': row[8]
                })

        return attentionData
    
    def getAttentionHistoryById(self, tokenId: str) -> List[Dict[str, Any]]:
        """
        Get historical attention data for a specific token.
        
        Args:
            tokenId: The token ID to get history for
            
        Returns:
            List of historical attention data
        """
        query = """
            SELECT 
                h.historyid,
                h.tokenid,
                h.attentionscore,
                h.recordedat
            FROM attentiondatahistory h
            WHERE h.tokenid = ?
            ORDER BY h.recordedat ASC
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (tokenId,))
            history_results = cursor.fetchall()
            
            # Get the latest record from attentiondata
            latest_query = """
                SELECT 
                    id,
                    tokenid,
                    attentionscore,
                    recordedat
                FROM attentiondata
                WHERE tokenid = ?
                ORDER BY recordedat DESC
                LIMIT 1
            """
            
            cursor.execute(latest_query, (tokenId,))
            latest_record = cursor.fetchone()
            
            # Convert results to list of dictionaries and handle aggregation by date
            history_data = {}
            
            # Process historical data first
            for row in history_results:
                date_part = row[3].split(' ')[0]  # Extract date part from datetime
                
                # For duplicate dates, keep the max score
                if date_part in history_data:
                    if float(row[2]) > float(history_data[date_part]['attentionScore']):
                        history_data[date_part] = {
                            'historyId': row[0],
                            'tokenId': row[1],
                            'attentionScore': float(row[2]),
                            'recordedAt': row[3],
                            'date': date_part
                        }
                else:
                    history_data[date_part] = {
                        'historyId': row[0],
                        'tokenId': row[1],
                        'attentionScore': float(row[2]),
                        'recordedAt': row[3],
                        'date': date_part
                    }
            
            # Add latest record if it exists and if the date doesn't exist in history
            if latest_record:
                date_part = latest_record[3].split(' ')[0]
                
                if date_part in history_data:
                    if float(latest_record[2]) > float(history_data[date_part]['attentionScore']):
                        history_data[date_part] = {
                            'historyId': latest_record[0],
                            'tokenId': latest_record[1],
                            'attentionScore': float(latest_record[2]),
                            'recordedAt': latest_record[3],
                            'date': date_part
                        }
                else:
                    history_data[date_part] = {
                        'historyId': latest_record[0],
                        'tokenId': latest_record[1],
                        'attentionScore': float(latest_record[2]),
                        'recordedAt': latest_record[3],
                        'date': date_part
                    }
            
            # Convert dictionary to list and sort by date
            result = list(history_data.values())
            result.sort(key=lambda x: x['date'])
            
            return result
    
    def getAttentionStatusOptions(self) -> List[str]:
        """
        Get all unique status options from the registry
        
        Returns:
            List of status values
        """
        query = """
            SELECT DISTINCT currentstatus
            FROM attentiontokenregistry
            WHERE currentstatus IS NOT NULL
        """
        
        with self.transaction() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            return [row[0] for row in results]
    
    def getChainOptions(self) -> List[str]:
        """
        Get all unique chain options from the registry
        
        Returns:
            List of chain values
        """
        query = """
            SELECT DISTINCT chain
            FROM attentiontokenregistry
            WHERE chain IS NOT NULL
        """
        
        with self.transaction() as cursor:
            cursor.execute(query)
            results = cursor.fetchall()
            
            return [row[0] for row in results] 