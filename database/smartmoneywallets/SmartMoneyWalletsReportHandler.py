from typing import List, Dict, Any, Optional
from database.operations.base_handler import BaseSQLiteHandler
from logs.logger import get_logger
import json
import sqlite3

logger = get_logger(__name__)

class SmartMoneyWalletsReportHandler(BaseSQLiteHandler):
    """
    Handler for smart money wallet report operations.
    Provides methods to query wallet PNL data and token details for reporting.
    """
    
    def __init__(self, conn_manager):
        """
        Initialize the handler with a connection manager.
        
        Args:
            conn_manager: Database connection manager instance
        """
        super().__init__(conn_manager)
    
    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """
        Execute a SQL query and return the results.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            
        Returns:
            List of tuples containing the query results
        """
        try:
            with self.conn_manager.transaction() as cursor:
                cursor.execute(query, params)
                return cursor.fetchall()
        except sqlite3.Error as e:
            logger.error(f"Database error executing query: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
    
    def getSmartMoneyWalletReport(self, 
                                 walletAddress: str,
                                 sortBy: str = "profitandloss",
                                 sortOrder: str = "desc") -> Dict[str, Any]:
        """
        Get smart money wallet report data for a specific wallet.
        Performs an inner join between smartmoneywallets and smwallettoppnltoken tables
        to get the wallet PNL and token-specific investment details.
        
        Args:
            walletAddress: The wallet address to get details for
            sortBy: Field to sort tokens by (default: profitandloss)
            sortOrder: Sort order (asc or desc)
            
        Returns:
            Dictionary containing wallet PNL data and token details
        """
        try:
            # Validate sort parameters
            valid_sort_fields = ["profitandloss", "tokenname", "amountinvested", "amounttakenout"]
            if sortBy not in valid_sort_fields:
                sortBy = "profitandloss"
                
            if sortOrder.lower() not in ["asc", "desc"]:
                sortOrder = "desc"
            
            # Map frontend sort field names to database column names
            sort_field_map = {
                "profitandloss": "t.unprocessedpnl",  # Updated to match actual column name
                "tokenname": "t.name",  # Updated to match actual column name
                "amountinvested": "t.amountinvested",
                "amounttakenout": "t.amounttakenout"
            }
            
            db_sort_field = sort_field_map.get(sortBy, "t.unprocessedpnl")  # Updated default
            
            # First, get the wallet data from smartmoneywallets table
            wallet_query = """
            SELECT 
                walletaddress,
                walletaddress as walletname,
                profitandloss
            FROM smartmoneywallets
            WHERE walletaddress = ?
            """
            
            wallet_params = (walletAddress,)
            wallet_result = self.execute_query(wallet_query, wallet_params)
            
            if not wallet_result:
                logger.warning(f"No wallet data found for address: {walletAddress}")
                return {"wallet": None, "tokens": []}
            
            # Create wallet data dictionary
            wallet_data = {
                "walletAddress": wallet_result[0][0],
                "walletName": wallet_result[0][1],
                "profitAndLoss": wallet_result[0][2]
            }
            
            # Now get the token data from smwallettoppnltoken table
            tokens_query = f"""
            SELECT 
                t.tokenid,
                t.name as tokenname,
                t.amountinvested,
                t.amounttakenout,
                t.unprocessedpnl as profitandloss
            FROM smwallettoppnltoken t
            WHERE t.walletaddress = ?
            ORDER BY {db_sort_field} {sortOrder}
            """
            
            tokens_params = (walletAddress,)
            tokens_results = self.execute_query(tokens_query, tokens_params)
            
            # Create token data list
            tokens = []
            for row in tokens_results:
                token = {
                    "tokenId": row[0],
                    "tokenName": row[1],
                    "amountInvested": row[2],
                    "amountTakenOut": row[3],
                    "profitAndLoss": row[4]
                }
                tokens.append(token)
            
            # Return combined data
            return {
                "wallet": wallet_data,
                "tokens": tokens
            }
            
        except Exception as e:
            logger.error(f"Error getting smart money wallet report: {str(e)}")
            return {"wallet": None, "tokens": [], "error": str(e)}
            
    def getTopSmartMoneyWallets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top smart money wallets by PNL.
        
        Args:
            limit: Maximum number of wallets to return
            
        Returns:
            List of dictionaries containing wallet data
        """
        try:
            query = """
            SELECT 
                walletaddress,
                walletaddress as walletname,
                profitandloss
            FROM smartmoneywallets
            ORDER BY CAST(profitandloss AS DECIMAL) DESC
            LIMIT ?
            """
            
            params = (limit,)
            results = self.execute_query(query, params)
            
            wallets = []
            for row in results:
                wallet = {
                    "walletAddress": row[0],
                    "walletName": row[1],
                    "profitAndLoss": row[2]
                }
                wallets.append(wallet)
                
            return wallets
            
        except Exception as e:
            logger.error(f"Error getting top smart money wallets: {str(e)}")
            return [] 