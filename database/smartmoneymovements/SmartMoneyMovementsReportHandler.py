from typing import List, Dict, Any, Optional
from database.operations.base_handler import BaseSQLiteHandler
from logs.logger import get_logger
import sqlite3
from datetime import datetime, timedelta
from actions.DexscrennerAction import DexScreenerAction

logger = get_logger(__name__)

# Configurable excluded token IDs (can be loaded from config file or database in production)
EXCLUDED_TOKEN_IDS = [
    "3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
    "native",
    "So11111111111111111111111111111111111111112",  # Wrapped SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
]
SQL_EXCLUDED_TOKENS = "(" + ",".join([f"'{token}'" for token in EXCLUDED_TOKEN_IDS]) + ")"

class SmartMoneyMovementsReportHandler(BaseSQLiteHandler):
    """
    Handler for smart money movements report operations.
    Provides methods to query wallet movement data for reporting.
    """
    
    def __init__(self, conn_manager):
        """
        Initialize the handler with a connection manager.
        
        Args:
            conn_manager: Database connection manager instance
        """
        super().__init__(conn_manager)
        self.dex_screener = DexScreenerAction()
    
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

    def getLastNDaysInvestmentReport(self, 
                                  wallet_address: str,
                                  days: int = 30,
                                  sort_by: str = "totalPnl",
                                  sort_order: str = "desc") -> Dict[str, Any]:
        """
        Get investment report for a wallet's token movements within specified time period.
        
        Args:
            wallet_address: Wallet address to analyze
            days: Number of days to look back
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)
            
        Returns:
            Dictionary with report data including summary and token details
        """
        try:
            # Validate sort parameters
            validSortFields = ["tokenaddress", "tokenname", "totalInvested", 
                                "totalTakenOut", "remainingCoins", "realizedPnl", 
                                "totalPnl", "pnlPercentage"]
            
            if sort_by not in validSortFields:
                sort_by = "totalPnl"
                
            if sort_order.lower() not in ["asc", "desc"]:
                sort_order = "desc"
            
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Query to get token movements for the wallet within date range
            query = f"""
            SELECT 
                tokenaddress,
                CASE 
                    WHEN COUNT(buytokenname) > 0 AND MAX(buytokenname) IS NOT NULL THEN MAX(buytokenname)
                    WHEN COUNT(selltokenname) > 0 AND MAX(selltokenname) IS NOT NULL THEN MAX(selltokenname)
                    ELSE 'Unknown'
                END AS tokenname,
                SUM(buytokenchange) AS total_buy_token,
                SUM(selltokenchange) AS total_sell_token,
                SUM(buyusdchange) AS total_buy_usd,
                SUM(sellusdchange) AS total_sell_usd
            FROM smartmoneymovements
            WHERE walletaddress = ?
            AND date >= ?
            AND date <= ?
            AND tokenaddress NOT IN {SQL_EXCLUDED_TOKENS}
            GROUP BY tokenaddress
            """
            
            params = (wallet_address, start_date, end_date)
            results = self.execute_query(query, params)
            
            # Process results
            tokens = []
            token_addresses = []
            
            for row in results:
                token_address = row[0]
                token_name = row[1] or "Unknown"
                total_buy_token = float(row[2]) if row[2] is not None else 0
                total_sell_token = float(row[3]) if row[3] is not None else 0
                total_buy_usd = float(row[4]) if row[4] is not None else 0
                total_sell_usd = float(row[5]) if row[5] is not None else 0
                
                remaining_coins = total_buy_token - total_sell_token
                realized_pnl = total_sell_usd - total_buy_usd
                
                token = {
                    "tokenAddress": token_address,
                    "tokenName": token_name,
                    "totalInvested": total_buy_usd,
                    "totalTakenOut": total_sell_usd,
                    "remainingCoins": remaining_coins,
                    "currentPrice": 0,  # Will be updated later
                    "remainingValue": 0,  # Will be calculated
                    "realizedPnl": realized_pnl,
                    "totalPnl": 0,  # Will be calculated
                    "pnlPercentage": 0  # Will be calculated
                }
                
                tokens.append(token)
                
                # Only fetch prices for tokens with remaining coins
                if remaining_coins > 0:
                    token_addresses.append(token_address)
            
            # Get current prices for tokens with remaining coins
            token_prices = {}
            if token_addresses:
                try:
                    token_price_data = self.dex_screener.getBatchTokenPrices(token_addresses, "solana")
                    
                    # Convert TokenPrice objects to simple price values
                    for token_id, token_price in token_price_data.items():
                        if token_price is not None:
                            token_prices[token_id] = token_price.price
                        else:
                            token_prices[token_id] = 0
                except Exception as e:
                    logger.error(f"Error fetching token prices: {str(e)}")
            
            # Calculate remaining value, total PNL, and PNL percentage
            wallet_summary = {
                "walletAddress": wallet_address,
                "totalInvested": 0,
                "totalTakenOut": 0,
                "totalRemainingValue": 0,
                "totalRealizedPnl": 0,
                "totalPnl": 0,
                "totalPnlPercentage": 0
            }
            
            for token in tokens:
                token_address = token["tokenAddress"]
                remaining_coins = token["remainingCoins"]
                
                # Get current price
                current_price = token_prices.get(token_address, 0)
                token["currentPrice"] = current_price
                
                # Calculate remaining value
                remaining_value = remaining_coins * current_price
                token["remainingValue"] = remaining_value
                
                # Calculate total PNL
                total_pnl = token["realizedPnl"] + remaining_value
                token["totalPnl"] = total_pnl
                
                # Calculate PNL percentage
                if token["totalInvested"] > 0:
                    token["pnlPercentage"] = (total_pnl / token["totalInvested"]) * 100
                
                # Update wallet summary
                wallet_summary["totalInvested"] += token["totalInvested"]
                wallet_summary["totalTakenOut"] += token["totalTakenOut"]
                wallet_summary["totalRemainingValue"] += remaining_value
                wallet_summary["totalRealizedPnl"] += token["realizedPnl"]
                wallet_summary["totalPnl"] += total_pnl
            
            # Calculate overall PNL percentage
            if wallet_summary["totalInvested"] > 0:
                wallet_summary["totalPnlPercentage"] = (wallet_summary["totalPnl"] / wallet_summary["totalInvested"]) * 100
            
            # Sort tokens based on requested field
            sort_field_map = {
                "tokenaddress": "tokenAddress",
                "tokenname": "tokenName",
                "totalInvested": "totalInvested",
                "totalTakenOut": "totalTakenOut",
                "remainingCoins": "remainingCoins",
                "realizedPnl": "realizedPnl",
                "totalPnl": "totalPnl",
                "pnlPercentage": "pnlPercentage"
            }
            
            sort_field = sort_field_map.get(sort_by, "totalPnl")
            tokens = sorted(tokens, key=lambda x: x[sort_field], reverse=(sort_order.lower() == "desc"))
            
            return {
                "wallet": wallet_summary,
                "tokens": tokens,
                "period": {
                    "days": days,
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat()
                }
            }
        
        except Exception as e:
            logger.error(f"Error generating wallet movement report: {str(e)}")
            return {
                "wallet": {
                    "walletAddress": wallet_address,
                    "totalInvested": 0,
                    "totalTakenOut": 0,
                    "totalRemainingValue": 0,
                    "totalRealizedPnl": 0,
                    "totalPnl": 0,
                    "totalPnlPercentage": 0
                },
                "tokens": [],
                "period": {
                    "days": days,
                    "startDate": start_date.isoformat() if 'start_date' in locals() else "",
                    "endDate": datetime.now().date().isoformat()
                },
                "error": str(e)
            } 

    def getTokenMovementsForWallet(self,
                                 wallet_address: str,
                                 token_address: str,
                                 days: int = 30) -> Dict[str, Any]:
        """
        Get daily movement data for a specific token in a wallet.
        
        Args:
            wallet_address: Wallet address to analyze
            token_address: Token address to get movements for
            days: Number of days to look back
            
        Returns:
            Dictionary with daily movement data
        """
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            # Query to get all daily movements directly
            query = f"""
            SELECT 
                date,
                tokenaddress,
                COALESCE(buytokenname, selltokenname, 'Unknown') AS tokenname,
                buytokenchange,
                selltokenchange,
                buyusdchange,
                sellusdchange
            FROM smartmoneymovements
            WHERE walletaddress = ?
            AND tokenaddress = ?
            AND date >= ?
            AND date <= ?
            AND tokenaddress NOT IN {SQL_EXCLUDED_TOKENS}
            ORDER BY date DESC
            """
            
            params = (wallet_address, token_address, start_date, end_date)
            results = self.execute_query(query, params)
            
            # Process results
            movements = []
            
            for row in results:
                date_str = row[0]
                token_address = row[1]
                token_name = row[2]
                buy_token_change = float(row[3]) if row[3] is not None else 0
                sell_token_change = float(row[4]) if row[4] is not None else 0
                buy_usd_change = float(row[5]) if row[5] is not None else 0
                sell_usd_change = float(row[6]) if row[6] is not None else 0
                
                movements.append({
                    "date": date_str,
                    "tokenAddress": token_address,
                    "tokenName": token_name,
                    "buyTokenChange": buy_token_change,
                    "sellTokenChange": sell_token_change,
                    "buyUsdChange": buy_usd_change,
                    "sellUsdChange": sell_usd_change
                })
            
            return {
                "movements": movements,
                "period": {
                    "days": days,
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting token movements: {str(e)}")
            return {
                "movements": [],
                "period": {
                    "days": days,
                    "startDate": start_date.isoformat() if 'start_date' in locals() else "",
                    "endDate": datetime.now().date().isoformat()
                },
                "error": str(e)
            } 

    def filterTokensByWalletBreakdown(self, tokens, category=None, type_filter=None, min_wallets=0, min_amount=0):
        """
        Filter tokens based on wallet category, type, count, and invested amount.
        
        Args:
            tokens: List of token data to filter
            category: Wallet category (0-300K, 300K-1M, >1M)
            type_filter: Wallet type filter (no-selling, <30%, >30%)
            min_wallets: Minimum number of wallets required
            min_amount: Minimum amount invested
            
        Returns:
            Filtered list of tokens
        """
        filtered_tokens = []
        
        # Map category to the appropriate property access
        category_map = {
            "0-300K": "cat1",
            "300K-1M": "cat2",
            ">1M": "cat3"
        }
        
        # Map type to index in categoryData
        type_map = {
            "no-selling": 0,  # No Selling
            "<30%": 1,        # < 30%
            ">30%": 2         # > 30%
        }
        
        cat_key = category_map.get(category)
        type_idx = type_map.get(type_filter)
        
        for token in tokens:
            # Skip filtering if no filters are set
            if not category and not type_filter and min_wallets <= 0 and min_amount <= 0:
                filtered_tokens.append(token)
                continue
                
            # Prepare wallet data as in renderWalletCategories function
            categoryData = [
                {
                    "name": "No Selling",
                    "cat1": {
                        "count": token.get("pnl_category_1_no_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_1_no_withdrawal_amount", 0) or 0
                    },
                    "cat2": {
                        "count": token.get("pnl_category_2_no_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_2_no_withdrawal_amount", 0) or 0
                    },
                    "cat3": {
                        "count": token.get("pnl_category_3_no_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_3_no_withdrawal_amount", 0) or 0
                    }
                },
                {
                    "name": "< 30%",
                    "cat1": {
                        "count": token.get("pnl_category_1_partial_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_1_partial_withdrawal_amount", 0) or 0
                    },
                    "cat2": {
                        "count": token.get("pnl_category_2_partial_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_2_partial_withdrawal_amount", 0) or 0
                    },
                    "cat3": {
                        "count": token.get("pnl_category_3_partial_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_3_partial_withdrawal_amount", 0) or 0
                    }
                },
                {
                    "name": "> 30%",
                    "cat1": {
                        "count": token.get("pnl_category_1_significant_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_1_significant_withdrawal_amount", 0) or 0
                    },
                    "cat2": {
                        "count": token.get("pnl_category_2_significant_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_2_significant_withdrawal_amount", 0) or 0
                    },
                    "cat3": {
                        "count": token.get("pnl_category_3_significant_withdrawal_count", 0) or 0,
                        "amount": token.get("pnl_category_3_significant_withdrawal_amount", 0) or 0
                    }
                }
            ]
            
            # Apply filters
            include_token = True
            
            # If both category and type are specified
            if category and type_filter and type_idx is not None and cat_key:
                wallet_count = categoryData[type_idx][cat_key]["count"]
                wallet_amount = categoryData[type_idx][cat_key]["amount"]
                
                if wallet_count < min_wallets:
                    include_token = False
                if min_amount > 0 and wallet_amount < min_amount:
                    include_token = False
            
            # If only category is specified
            elif category and cat_key:
                # Sum up wallets across all types for this category
                total_count = sum(data[cat_key]["count"] for data in categoryData)
                total_amount = sum(data[cat_key]["amount"] for data in categoryData)
                
                if total_count < min_wallets:
                    include_token = False
                if min_amount > 0 and total_amount < min_amount:
                    include_token = False
            
            # If only type is specified
            elif type_filter and type_idx is not None:
                # Sum up wallets across all categories for this type
                total_count = sum(categoryData[type_idx][cat]["count"] for cat in ["cat1", "cat2", "cat3"])
                total_amount = sum(categoryData[type_idx][cat]["amount"] for cat in ["cat1", "cat2", "cat3"])
                
                if total_count < min_wallets:
                    include_token = False
                if min_amount > 0 and total_amount < min_amount:
                    include_token = False
            
            # If only min_wallets or min_amount is specified
            elif min_wallets > 0 or min_amount > 0:
                # Sum up all wallets across all categories and types
                total_count = sum(data[cat]["count"] for data in categoryData for cat in ["cat1", "cat2", "cat3"])
                total_amount = sum(data[cat]["amount"] for data in categoryData for cat in ["cat1", "cat2", "cat3"])
                
                if total_count < min_wallets:
                    include_token = False
                if min_amount > 0 and total_amount < min_amount:
                    include_token = False
            
            if include_token:
                filtered_tokens.append(token)
                
        return filtered_tokens 