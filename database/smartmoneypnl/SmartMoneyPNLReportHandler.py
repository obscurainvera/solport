from typing import List, Dict, Any, Optional, Tuple, Set
from database.operations.base_handler import BaseSQLiteHandler
from logs.logger import get_logger
import sqlite3
from datetime import datetime, timedelta
from actions.DexscrennerAction import DexScreenerAction
from functools import lru_cache
import time

logger = get_logger(__name__)

# Constants for excluded token IDs
EXCLUDED_TOKEN_IDS = [
    "native",
    "So11111111111111111111111111111111111111112",  # Wrapped SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
]

# SQL query fragments for reuse
SQL_EXCLUDED_TOKENS = "(" + ",".join([f"'{token}'" for token in EXCLUDED_TOKEN_IDS]) + ")"

class SmartMoneyPNLReportHandler(BaseSQLiteHandler):
    """
    Handler for Smart Money PNL report operations.
    Provides methods to analyze and report on wallet PNL performance.
    """
    
    def __init__(self, conn_manager):
        """
        Initialize the handler with a connection manager.
        
        Args:
            conn_manager: Database connection manager instance
        """
        super().__init__(conn_manager)
        self.dex_screener = DexScreenerAction()
        
    # Helper methods for modularity and reusability
    def _get_date_range(self, days: int) -> Tuple[datetime.date, datetime.date]:
        """
        Calculate the date range for the report.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Tuple of (start_date, end_date)
        """
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date
    
    def _get_sort_parameters(self, sort_by: str, sort_order: str) -> Tuple[str, str]:
        """
        Validate and normalize sort parameters.
        
        Args:
            sort_by: Field to sort by
            sort_order: Sort order
            
        Returns:
            Tuple of (sort_field, sort_order)
        """
        valid_sort_fields = {
            "pnl": "realized_pnl",  # Use realized_pnl for initial sorting in SQL
            "invested": "total_invested", 
            "tokens": "unique_token_count",
            "trades": "smw.tradecount"
        }
        
        valid_sort_orders = ["asc", "desc"]
        
        # Default to PNL sorting if invalid field provided
        sort_field = valid_sort_fields.get(sort_by.lower(), "realized_pnl")
        
        # Default to descending if invalid order provided
        sort_order = sort_order.lower() if sort_order.lower() in valid_sort_orders else "desc"
        
        return sort_field, sort_order
    
    @lru_cache(maxsize=32)
    def _get_wallet_token_balances(self, wallet_address: str, start_date, end_date) -> Dict[str, float]:
        """
        Get token balances for a wallet within a date range.
        Uses caching to avoid redundant queries.
        
        Args:
            wallet_address: Wallet address to query
            start_date: Start date for query
            end_date: End date for query
            
        Returns:
            Dictionary mapping token addresses to balances
        """
        query = f"""
        SELECT 
            tokenaddress,
            SUM(buytokenchange) - SUM(selltokenchange) AS remaining_balance
        FROM 
            smartmoneymovements
        WHERE 
            walletaddress = ?
            AND date >= ?
            AND date <= ?
            AND tokenaddress NOT IN {SQL_EXCLUDED_TOKENS}
        GROUP BY 
            tokenaddress
        HAVING
            (SUM(buytokenchange) - SUM(selltokenchange)) > 0
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (wallet_address, start_date, end_date))
            results = cursor.fetchall()
            
            token_balances = {}
            for row in results:
                token_address = row['tokenaddress']
                balance = float(row['remaining_balance']) if row['remaining_balance'] else 0
                if balance > 0:
                    token_balances[token_address] = balance
                    
            return token_balances
    
    def _calculate_wallet_values(self, wallets: List[Dict], wallet_tokens: Dict[str, Dict[str, float]], 
                               token_prices: Dict[str, Any]) -> None:
        """
        Calculate remaining value and total PNL for each wallet.
        
        Args:
            wallets: List of wallet dictionaries to update
            wallet_tokens: Dictionary mapping wallet addresses to token balances
            token_prices: Dictionary mapping token addresses to price objects
        """
        for wallet in wallets:
            wallet_address = wallet['walletAddress']
            remaining_tokens = wallet_tokens.get(wallet_address, {})
            
            remaining_value = 0
            for token_id, balance in remaining_tokens.items():
                token_price_obj = token_prices.get(token_id)
                if token_price_obj:
                    token_price = token_price_obj.price
                    token_value = balance * token_price
                    remaining_value += token_value
            
            wallet['remainingValue'] = remaining_value
            wallet['totalPnl'] = wallet['realizedPnl'] + remaining_value
    
    def getTopPNLWallets(self, days: int = 30, limit: int = 100, sortBy: str = "pnl", sortOrder: str = "desc", minTotalPnl: float = None, minWalletPnl: float = None) -> Dict[str, Any]:
        """
        Get top PNL wallets for the specified time period.
        
        Args:
            days: Number of days to look back (7, 30, or 90)
            limit: Maximum number of wallets to return
            sortBy: Field to sort by (pnl, invested, tokens, trades)
            sortOrder: Sort order (asc or desc)
            minTotalPnl: Minimum total PNL filter (calculated PNL including remaining value)
            minWalletPnl: Minimum wallet PNL filter (historical PNL from smartmoneywallets table)
            
        Returns:
            Dictionary with report data including wallets and their PNL metrics
        """
        try:
            start_time = time.time()
            logger.info(f"Starting top PNL wallets report generation for {days} days")
            
            # Get date range and sort parameters
            start_date, end_date = self._get_date_range(days)
            sort_field, sort_order = self._get_sort_parameters(sortBy, sortOrder)
            
            # Prepare wallet PNL filter
            wallet_pnl_filter = ""
            if minWalletPnl is not None and minWalletPnl > 0:
                wallet_pnl_filter = f"AND smw.profitandloss >= {minWalletPnl}"
            
            # Build the optimized query - uses a single pass through the data
            # This query is optimized for large datasets by:
            # 1. Using a CTE to calculate metrics in one pass
            # 2. Minimizing the data scanned by filtering early
            # 3. Using efficient aggregation functions
            # Format the query with the wallet PNL filter
            query = f"""            
            WITH wallet_metrics AS (
                SELECT 
                    smm.walletaddress,
                    SUM(smm.buyusdchange) AS total_invested,
                    SUM(smm.sellusdchange) AS total_taken_out,
                    COUNT(DISTINCT smm.tokenaddress) AS unique_token_count,
                    -- Check if wallet has any tokens with positive remaining balance
                    EXISTS (
                        SELECT 1 FROM smartmoneymovements sub
                        WHERE sub.walletaddress = smm.walletaddress
                        AND sub.tokenaddress NOT IN {SQL_EXCLUDED_TOKENS}
                        AND sub.date >= ? AND sub.date <= ?
                        GROUP BY sub.tokenaddress
                        HAVING SUM(sub.buytokenchange) - SUM(sub.selltokenchange) > 0
                        LIMIT 1
                    ) AS has_remaining_tokens
                FROM 
                    smartmoneymovements smm
                WHERE 
                    smm.date >= ?
                    AND smm.date <= ?
                GROUP BY 
                    smm.walletaddress
                HAVING
                    SUM(smm.buyusdchange) > 0  -- Filter out wallets with no investment
            )
            SELECT 
                wm.walletaddress,
                wm.total_invested,
                wm.total_taken_out,
                wm.unique_token_count,
                wm.total_taken_out - wm.total_invested AS realized_pnl,
                smw.profitandloss AS wallet_pnl,
                smw.tradecount
            FROM 
                wallet_metrics wm
            LEFT JOIN 
                smartmoneywallets smw ON wm.walletaddress = smw.walletaddress
            WHERE
                wm.has_remaining_tokens = 1  -- Only include wallets with remaining tokens
                {wallet_pnl_filter}
            ORDER BY 
                {sort_field} {sort_order.upper()}
            LIMIT ?
            """
            
            # Execute the query - note the parameters now include start_date and end_date twice
            # First pair is for the subquery that checks for remaining tokens
            # Second pair is for the main query date filtering
            params = (start_date, end_date, start_date, end_date, limit)
            
            with self.transaction() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                query_time = time.time()
                logger.info(f"Query execution completed in {query_time - start_time:.2f} seconds, processing {len(results)} wallets")
                
                # Process results
                wallets = []
                wallet_tokens = {}
                token_addresses_to_fetch = set()
                
                # First pass: extract basic wallet data
                for row in results:
                    wallet_address = row['walletaddress']
                    total_invested = float(row['total_invested']) if row['total_invested'] else 0
                    total_taken_out = float(row['total_taken_out']) if row['total_taken_out'] else 0
                    unique_token_count = row['unique_token_count']
                    realized_pnl = float(row['realized_pnl']) if row['realized_pnl'] else 0
                    wallet_pnl = float(row['wallet_pnl']) if row['wallet_pnl'] else 0
                    trade_count = row['tradecount'] if row['tradecount'] else 0
                    
                    # Store the wallet data
                    wallet = {
                        'walletAddress': wallet_address,
                        'totalInvested': total_invested,
                        'totalTakenOut': total_taken_out,
                        'uniqueTokenCount': unique_token_count,
                        'realizedPnl': realized_pnl,
                        'remainingValue': 0,  # Will be updated after price fetching
                        'totalPnl': realized_pnl,  # Initialize with realized PNL
                        'tradeCount': trade_count,
                        'walletPnl': wallet_pnl
                    }
                    
                    wallets.append(wallet)
                    
                    # Get token balances for this wallet
                    token_balances = self._get_wallet_token_balances(wallet_address, start_date, end_date)
                    wallet_tokens[wallet_address] = token_balances
                    
                    # Collect token addresses for price fetching
                    token_addresses_to_fetch.update(token_balances.keys())
                
                token_fetch_time = time.time()
                logger.info(f"Token balance extraction completed in {token_fetch_time - query_time:.2f} seconds")
                
                # Fetch current prices for all tokens with remaining balances
                if token_addresses_to_fetch:
                    try:
                        logger.info(f"Fetching prices for {len(token_addresses_to_fetch)} tokens")
                        token_prices = self.dex_screener.getBatchTokenPrices(list(token_addresses_to_fetch))
                        
                        # Calculate remaining value and total PNL for each wallet
                        self._calculate_wallet_values(wallets, wallet_tokens, token_prices)
                    
                    except Exception as e:
                        logger.error(f"Error fetching token prices: {str(e)}")
                        # If price fetching fails, keep total PNL as realized PNL
                
                # Apply total PNL filter if specified
                if minTotalPnl is not None and minTotalPnl > 0:
                    logger.info(f"Filtering wallets by minimum total PNL: {minTotalPnl}")
                    wallets = [wallet for wallet in wallets if wallet['totalPnl'] >= minTotalPnl]
                
                # Re-sort the wallets based on the calculated total PNL if requested
                if sortBy.lower() == "pnl":
                    logger.info("Re-sorting results by total PNL after price calculations")
                    wallets.sort(
                        key=lambda x: x['totalPnl'], 
                        reverse=(sort_order == "desc")
                    )
                
                end_time = time.time()
                logger.info(f"Report generation completed in {end_time - start_time:.2f} seconds")
                
                return {
                    'wallets': wallets,
                    'period': {
                        'days': days,
                        'startDate': start_date.isoformat(),
                        'endDate': end_date.isoformat()
                    },
                    'metrics': {
                        'executionTimeSeconds': round(end_time - start_time, 2),
                        'walletCount': len(wallets),
                        'tokenCount': len(token_addresses_to_fetch)
                    }
                }
                
        except Exception as e:
            logger.error(f"Error generating top PNL wallets report: {str(e)}")
            return {
                'wallets': [],
                'period': {
                    'days': days,
                    'startDate': start_date.isoformat() if 'start_date' in locals() else "",
                    'endDate': datetime.now().date().isoformat()
                },
                'error': str(e)
            }
            
    def _get_wallet_summary(self, wallet_address: str, start_date: datetime.date, end_date: datetime.date) -> Optional[Dict[str, Any]]:
        """
        Get wallet summary information including total invested, taken out, and unique token count.
        
        Args:
            wallet_address: Wallet address to analyze
            start_date: Start date for query
            end_date: End date for query
            
        Returns:
            Dictionary with wallet summary information or None if no data
        """
        query = """
        SELECT 
            SUM(buyusdchange) AS total_invested,
            SUM(sellusdchange) AS total_taken_out,
            COUNT(DISTINCT tokenaddress) AS unique_token_count
        FROM 
            smartmoneymovements
        WHERE 
            walletaddress = ?
            AND date >= ?
            AND date <= ?
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (wallet_address, start_date, end_date))
            row = cursor.fetchone()
            
            if not row or not row['total_invested']:
                return None
                
            return {
                'totalInvested': float(row['total_invested']) if row['total_invested'] else 0,
                'totalTakenOut': float(row['total_taken_out']) if row['total_taken_out'] else 0,
                'uniqueTokenCount': row['unique_token_count'] if row['unique_token_count'] else 0
            }
    
    def _get_wallet_info(self, wallet_address: str) -> Dict[str, Any]:
        """
        Get wallet information from smartmoneywallets table.
        
        Args:
            wallet_address: Wallet address to query
            
        Returns:
            Dictionary with wallet information
        """
        query = """
        SELECT 
            profitandloss,
            tradecount,
            firstseen,
            lastseen
        FROM 
            smartmoneywallets
        WHERE 
            walletaddress = ?
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (wallet_address,))
            row = cursor.fetchone()
            
            if not row:
                return {
                    'profitAndLoss': 0,
                    'tradeCount': 0,
                    'firstSeen': None,
                    'lastSeen': None
                }
                
            return {
                'profitAndLoss': float(row['profitandloss']) if row['profitandloss'] else 0,
                'tradeCount': row['tradecount'] if row['tradecount'] else 0,
                'firstSeen': row['firstseen'],
                'lastSeen': row['lastseen']
            }
    
    def _get_token_breakdown(self, wallet_address: str, start_date: datetime.date, end_date: datetime.date) -> List[Dict[str, Any]]:
        """
        Get token-level breakdown for a wallet.
        
        Args:
            wallet_address: Wallet address to analyze
            start_date: Start date for query
            end_date: End date for query
            
        Returns:
            List of token data dictionaries
        """
        query = f"""
        SELECT 
            tokenaddress,
            COALESCE(MAX(buytokenname), MAX(selltokenname), 'Unknown') AS token_name,
            SUM(buytokenchange) AS buy_token_change,
            SUM(selltokenchange) AS sell_token_change,
            SUM(buyusdchange) AS buy_usd_change,
            SUM(sellusdchange) AS sell_usd_change
        FROM 
            smartmoneymovements
        WHERE 
            walletaddress = ?
            AND date >= ?
            AND date <= ?
            AND tokenaddress NOT IN {SQL_EXCLUDED_TOKENS}
        GROUP BY 
            tokenaddress
        HAVING
            SUM(buytokenchange) - SUM(selltokenchange) != 0  -- Only include tokens with non-zero balance
        ORDER BY 
            SUM(buyusdchange) DESC
        """
        
        with self.transaction() as cursor:
            cursor.execute(query, (wallet_address, start_date, end_date))
            rows = cursor.fetchall()
            
            tokens = []
            token_addresses_to_fetch = []
            
            for row in rows:
                token_address = row['tokenaddress']
                token_name = row['token_name']
                buy_token_change = float(row['buy_token_change']) if row['buy_token_change'] else 0
                sell_token_change = float(row['sell_token_change']) if row['sell_token_change'] else 0
                buy_usd_change = float(row['buy_usd_change']) if row['buy_usd_change'] else 0
                sell_usd_change = float(row['sell_usd_change']) if row['sell_usd_change'] else 0
                
                remaining_balance = buy_token_change - sell_token_change
                token_realized_pnl = sell_usd_change - buy_usd_change
                
                token = {
                    'tokenAddress': token_address,
                    'tokenName': token_name,
                    'buyTokenChange': buy_token_change,
                    'sellTokenChange': sell_token_change,
                    'buyUsdChange': buy_usd_change,
                    'sellUsdChange': sell_usd_change,
                    'remainingBalance': remaining_balance,
                    'realizedPnl': token_realized_pnl,
                    'currentPrice': 0,
                    'remainingValue': 0,
                    'totalPnl': token_realized_pnl
                }
                
                tokens.append(token)
                
                # Only fetch prices for tokens with remaining balance
                if remaining_balance > 0:
                    token_addresses_to_fetch.append(token_address)
            
            return tokens, token_addresses_to_fetch
    
    def _update_token_prices(self, tokens: List[Dict[str, Any]], token_prices: Dict[str, Any]) -> float:
        """
        Update token data with current prices and calculate remaining value.
        
        Args:
            tokens: List of token dictionaries to update
            token_prices: Dictionary mapping token addresses to price objects
            
        Returns:
            Total remaining value across all tokens
        """
        total_remaining_value = 0
        
        for token in tokens:
            token_address = token['tokenAddress']
            token_price_obj = token_prices.get(token_address)
            
            if token_price_obj and token['remainingBalance'] > 0:
                token_price = token_price_obj.price
                token['currentPrice'] = token_price
                
                token_remaining_value = token['remainingBalance'] * token_price
                token['remainingValue'] = token_remaining_value
                token['totalPnl'] = token['realizedPnl'] + token_remaining_value
                
                total_remaining_value += token_remaining_value
        
        return total_remaining_value
    
    def getWalletPNLDetails(self,
                           wallet_address: str,
                           days: int = 30) -> Dict[str, Any]:
        """
        Get detailed PNL information for a specific wallet.
        
        Args:
            wallet_address: Wallet address to analyze
            days: Number of days to look back (7, 30, or 90)
            
        Returns:
            Dictionary with wallet PNL details including token-level breakdown
        """
        try:
            start_time = time.time()
            logger.info(f"Starting wallet PNL details analysis for {wallet_address} over {days} days")
            
            # Get date range
            start_date, end_date = self._get_date_range(days)
            
            # Get wallet summary
            wallet_summary = self._get_wallet_summary(wallet_address, start_date, end_date)
            if not wallet_summary:
                logger.warning(f"No movement data found for wallet {wallet_address}")
                return None
            
            # Calculate realized PNL
            realized_pnl = wallet_summary['totalTakenOut'] - wallet_summary['totalInvested']
            
            # Get wallet info from smartmoneywallets table
            wallet_info = self._get_wallet_info(wallet_address)
            
            # Get token breakdown
            summary_time = time.time()
            logger.info(f"Wallet summary retrieved in {summary_time - start_time:.2f} seconds")
            
            tokens, token_addresses_to_fetch = self._get_token_breakdown(wallet_address, start_date, end_date)
            
            token_time = time.time()
            logger.info(f"Token breakdown retrieved in {token_time - summary_time:.2f} seconds, found {len(tokens)} tokens")
            
            # Fetch current prices for tokens with remaining balances
            remaining_value = 0
            if token_addresses_to_fetch:
                try:
                    logger.info(f"Fetching prices for {len(token_addresses_to_fetch)} tokens")
                    token_prices = self.dex_screener.getBatchTokenPrices(token_addresses_to_fetch)
                    
                    # Update token data with current prices
                    remaining_value = self._update_token_prices(tokens, token_prices)
                    
                except Exception as e:
                    logger.error(f"Error fetching token prices: {str(e)}")
                    # If price fetching fails, keep remaining value at 0
            
            # Calculate total PNL
            total_pnl = realized_pnl + remaining_value
            
            # Sort tokens by total PNL
            tokens.sort(key=lambda x: x['totalPnl'], reverse=True)
            
            price_time = time.time()
            logger.info(f"Price fetching and calculations completed in {price_time - token_time:.2f} seconds")
            
            result = {
                'wallet': {
                    'walletAddress': wallet_address,
                    'totalInvested': wallet_summary['totalInvested'],
                    'totalTakenOut': wallet_summary['totalTakenOut'],
                    'uniqueTokenCount': wallet_summary['uniqueTokenCount'],
                    'realizedPnl': realized_pnl,
                    'remainingValue': remaining_value,
                    'totalPnl': total_pnl,
                    'tradeCount': wallet_info['tradeCount'],
                    'walletPnl': wallet_info['profitAndLoss'],
                    'firstSeen': wallet_info['firstSeen'],
                    'lastSeen': wallet_info['lastSeen']
                },
                'tokens': tokens,
                'period': {
                    'days': days,
                    'startDate': start_date.isoformat(),
                    'endDate': end_date.isoformat()
                },
                'metrics': {
                    'executionTimeSeconds': round(time.time() - start_time, 2),
                    'tokenCount': len(tokens)
                }
            }
            
            end_time = time.time()
            logger.info(f"Wallet PNL details analysis completed in {end_time - start_time:.2f} seconds")
            
            return result
                
        except Exception as e:
            logger.error(f"Error getting wallet PNL details: {str(e)}")
            return None
