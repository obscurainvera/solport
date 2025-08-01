from typing import Dict, List, Any, Tuple
from database.operations.base_handler import BaseSQLiteHandler
from logs.logger import get_logger
from datetime import datetime, timedelta
from actions.DexscrennerAction import DexScreenerAction
import time
from tenacity import retry, stop_after_attempt, wait_exponential
from cache import cache_manager

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

class SmartMoneyPNLReportHandler(BaseSQLiteHandler):
    def __init__(self, conn_manager):
        super().__init__(conn_manager)
        self.dex_screener = DexScreenerAction()
        self._create_indexes()

    def _create_indexes(self):
        """Create database indexes for optimal query performance."""
        try:
            with self.conn_manager.transaction() as cursor:
                # Index for date-based queries on smartmoneymovements
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_smartmoneymovements_date_wallet_token 
                    ON smartmoneymovements(date, walletaddress, tokenaddress)
                """)
                
                # Index for wallet-based queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_smartmoneymovements_wallet_date 
                    ON smartmoneymovements(walletaddress, date)
                """)
                
                # Index for token-based queries
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_smartmoneymovements_token_date 
                    ON smartmoneymovements(tokenaddress, date)
                """)
                
                # Index for smartmoneywallets table
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_smartmoneywallets_address 
                    ON smartmoneywallets(walletaddress)
                """)
                
                # Index for walletsinvested table
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_walletsinvested_token_status 
                    ON walletsinvested(tokenid, status)
                """)
                
                logger.info("Database indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating database indexes: {str(e)}")

    def _get_date_range(self, days: int) -> Tuple[datetime.date, datetime.date]:
        """Calculate the date range for the report."""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date

    def _get_sort_parameters(self, sort_by: str, sort_order: str) -> Tuple[str, str]:
        """Validate and normalize sort parameters."""
        valid_sort_fields = {
            "pnl": "totalPnl",
            "invested": "totalInvested",
            "tokens": "uniqueTokenCount",
            "trades": "tradeCount"
        }
        valid_sort_orders = ["asc", "desc"]
        sort_field = valid_sort_fields.get(sort_by.lower(), "totalPnl")
        sort_order = sort_order.lower() if sort_order.lower() in valid_sort_orders else "desc"
        return sort_field, sort_order

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _fetch_token_prices(self, token_addresses: List[str]) -> Dict[str, Any]:
        """Fetch token prices using enterprise cache manager."""
        def fetch_function(tokens: List[str]) -> Dict[str, Any]:
            """Internal function to fetch uncached token prices."""
            return self.dex_screener.getBatchTokenPrices(tokens)
        
        return cache_manager.get_token_prices(token_addresses, fetch_function)

    def getTopPNLWallets(self, days: int = 30, limit: int = 100, sortBy: str = "pnl", sortOrder: str = "desc", minTotalPnl: float = None, minWalletPnl: float = None, winRateThreshold: float = None) -> Dict[str, Any]:
        """
        Get top PNL wallets for the specified period with optimized data fetching and processing.

        Args:
            days: Number of days to look back.
            limit: Maximum number of wallets to return.
            sortBy: Field to sort by (pnl, invested, tokens, trades).
            sortOrder: Sort order (asc or desc).
            minTotalPnl: Minimum total PNL filter.
            minWalletPnl: Minimum wallet PNL filter.
            winRateThreshold: Minimum investment threshold for win rate calculation.

        Returns:
            Dictionary with wallet PNL metrics, metadata, and win rate statistics.
        """
        # Cache key parameters
        cache_params = {
            "type": "top_pnl",
            "days": days,
            "limit": limit,
            "sortBy": sortBy,
            "sortOrder": sortOrder,
            "minTotalPnl": minTotalPnl,
            "minWalletPnl": minWalletPnl,
            "winRateThreshold": winRateThreshold
        }
        
        def generate_report():
            """Internal function to generate fresh report data."""
            try:
                start_time = time.time()
                logger.info(f"Starting top PNL wallets report generation for {days} days")
                
                start_date, end_date = self._get_date_range(days)
                sort_field, sort_order = self._get_sort_parameters(sortBy, sortOrder)

                # Optimized query to fetch only necessary transaction data with pre-filtering
                query = f"""
                SELECT 
                    walletaddress,
                    tokenaddress,
                    SUM(buytokenchange) AS total_buytoken,
                    SUM(selltokenchange) AS total_selltoken,
                    SUM(buyusdchange) AS total_buyusd,
                    SUM(sellusdchange) AS total_sellusd
                FROM 
                    smartmoneymovements
                WHERE 
                    date >= ? AND date <= ?
                    AND tokenaddress NOT IN {SQL_EXCLUDED_TOKENS}
                    AND (buyusdchange > 0 OR sellusdchange > 0)
                GROUP BY 
                    walletaddress, tokenaddress
                HAVING 
                    (SUM(buyusdchange) > 0 OR SUM(sellusdchange) > 0)
                """
                
                with self.transaction() as cursor:
                    cursor.execute(query, (start_date, end_date))
                    results = cursor.fetchall()

                    wallet_data = {}
                    for row in results:
                        wallet_address = row['walletaddress']  # Already normalized
                        token_address = row['tokenaddress']
                        total_buytoken = float(row['total_buytoken'] or 0)
                        total_selltoken = float(row['total_selltoken'] or 0)
                        total_buyusd = float(row['total_buyusd'] or 0)
                        total_sellusd = float(row['total_sellusd'] or 0)
                        remaining_balance = total_buytoken - total_selltoken

                        # CRITICAL FIX: Only include tokens where there was actual investment in the time range
                        # Skip tokens with zero buyusdchange (bought before period but sold during period)
                        if total_buyusd <= 0:
                            continue

                        if wallet_address not in wallet_data:
                            wallet_data[wallet_address] = {
                                'total_invested': 0,
                                'total_taken_out': 0,
                                'unique_tokens': set(),
                                'token_balances': {}
                            }

                        wallet = wallet_data[wallet_address]
                        wallet['total_invested'] += total_buyusd
                        wallet['total_taken_out'] += total_sellusd
                        wallet['unique_tokens'].add(token_address)
                        if remaining_balance > 0:
                            wallet['token_balances'][token_address] = remaining_balance

                    wallets = []
                    for wallet_address, data in wallet_data.items():
                        # Only include wallets that have actual investments (total_invested > 0)
                        # This fixes the PNL calculation bug where tokens bought before the time period
                        # but sold within it would show incorrect positive PNL
                        if data['total_invested'] > 0 and data['token_balances']:
                            realized_pnl = data['total_taken_out'] - data['total_invested']
                            wallets.append({
                                'walletAddress': wallet_address,
                                'totalInvested': data['total_invested'],
                                'totalTakenOut': data['total_taken_out'],
                                'uniqueTokenCount': len(data['unique_tokens']),
                                'realizedPnl': realized_pnl,
                                'tokenBalances': data['token_balances'],
                                'remainingValue': 0,
                                'totalPnl': realized_pnl,
                                'tradeCount': 0,
                                'walletPnl': 0
                            })

                    if wallets:
                        # Optimize wallet info query by only fetching data for relevant wallets
                        wallet_addresses = [w['walletAddress'] for w in wallets]
                        placeholders = ','.join(['?' for _ in wallet_addresses])
                        wallet_info_query = f"""
                        SELECT walletaddress, profitandloss, tradecount
                        FROM smartmoneywallets
                        WHERE walletaddress IN ({placeholders})
                        """
                        cursor.execute(wallet_info_query, wallet_addresses)
                        wallet_info = {row['walletaddress']: row for row in cursor.fetchall()}
                        
                        for wallet in wallets:
                            info = wallet_info.get(wallet['walletAddress'], {}) 
                            if not info:
                                logger.warning(f"No data found in smartmoneywallets for wallet {wallet['walletAddress']}")
                            try:
                                wallet['walletPnl'] = float(info['profitandloss'])
                            except ValueError:
                                logger.info(f"Invalid profitandloss value for wallet {wallet['walletAddress']}: {info.get('profitandloss')}")
                                wallet['walletPnl'] = 0
                                
                            try:
                                wallet['tradeCount'] = int(info['tradecount'])
                            except ValueError:
                                logger.info(f"Invalid tradecount value for wallet {wallet['walletAddress']}: {info.get('tradecount')}")
                                wallet['tradeCount'] = 0

                    if minWalletPnl is not None and minWalletPnl > 0:
                        wallets = [w for w in wallets if w['walletPnl'] >= minWalletPnl]

                    # Optimize token price fetching by only getting prices for tokens with balances
                    all_token_addresses = set()
                    for wallet in wallets:
                        all_token_addresses.update(wallet['tokenBalances'].keys())

                    # Batch token price fetching with error handling
                    token_prices = {}
                    if all_token_addresses:
                        try:
                            token_prices = self._fetch_token_prices(list(all_token_addresses))
                        except Exception as e:
                            logger.warning(f"Failed to fetch token prices, continuing without prices: {str(e)}")
                            token_prices = {}

                    for wallet in wallets:
                        remaining_value = 0
                        for token, balance in wallet['tokenBalances'].items():
                            token_price = token_prices.get(token)
                            price = token_price.price if token_price and token_price.marketCap > 10000 else 0
                            current_remaining_value = balance * price
                            if token_price and token_price.marketCap > current_remaining_value:
                                remaining_value += current_remaining_value
                        wallet['remainingValue'] = remaining_value
                        wallet['totalPnl'] = wallet['realizedPnl'] + remaining_value

                    if minTotalPnl is not None and minTotalPnl > 0:
                        wallets = [w for w in wallets if w['totalPnl'] >= minTotalPnl]

                    wallets.sort(key=lambda x: x[sort_field], reverse=(sort_order == "desc"))
                    wallets = wallets[:limit]

                end_time = time.time()
                logger.info(f"Report generated in {end_time - start_time:.2f} seconds")

                # Calculate win rate metrics if threshold is provided
                win_rate_metrics = {}
                if winRateThreshold is not None and winRateThreshold > 0:
                    # Find all wallets that meet the investment threshold
                    threshold_wallets = [w for w in wallets if w['totalInvested'] >= winRateThreshold]
                    threshold_count = len(threshold_wallets)
                    
                    # Count how many of those had positive PNL (wins)
                    win_rate_count = len([w for w in threshold_wallets if w['totalPnl'] > 0])
                    
                    # Calculate win rate percentage
                    win_rate = (win_rate_count / threshold_count * 100) if threshold_count > 0 else 0
                    
                    win_rate_metrics = {
                        'winRate': round(win_rate, 2),
                        'thresholdCount': threshold_count,
                        'winRateCount': win_rate_count,
                        'threshold': winRateThreshold
                    }

                result = {
                    'wallets': wallets,
                    'period': {
                        'days': days,
                        'startDate': start_date.isoformat(),
                        'endDate': end_date.isoformat()
                    },
                    'metrics': {
                        'executionTimeSeconds': round(end_time - start_time, 2),
                        'walletCount': len(wallets),
                        'tokenCount': len(all_token_addresses),
                        **win_rate_metrics
                    }
                }
                
                return result

            except Exception as e:
                logger.error(f"Error generating PNL report: {str(e)}")
                return {
                    'wallets': [],
                    'period': {'days': days, 'startDate': '', 'endDate': datetime.now().date().isoformat()},
                    'error': str(e)
                }
        
        # Use cache manager for report caching
        return cache_manager.get_report(cache_params, generate_report)

    def getWalletPNLDetails(self, wallet_address: str, days: int = 30, sort_by: str = "totalPnl", sort_order: str = "desc") -> Dict[str, Any]:
        """
        Get detailed PNL information for a specific wallet, including token-level breakdown.

        Args:
            wallet_address: Wallet address to analyze.
            days: Number of days to look back.
            sort_by: Field to sort tokens by (totalPnl, pnlPercentage, totalInvested, etc.).
            sort_order: Sort order (asc or desc).

        Returns:
            Dictionary with detailed wallet PNL data, including token details.
        """
        # Normalize input wallet address
        wallet_address = wallet_address.strip().lower()
        
        # Cache key parameters
        cache_params = {
            "type": "wallet_details",
            "wallet_address": wallet_address,
            "days": days,
            "sort_by": sort_by,
            "sort_order": sort_order
        }
        
        def generate_wallet_report():
            """Internal function to generate fresh wallet report data."""
            try:
                start_time = time.time()
                start_date, end_date = self._get_date_range(days)

                # Query to fetch detailed token data with normalized wallet address
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
                    TRIM(LOWER(walletaddress)) = ?
                    AND date >= ? AND date <= ?
                    AND tokenaddress NOT IN {SQL_EXCLUDED_TOKENS}
                GROUP BY 
                    tokenaddress
                """
                with self.transaction() as cursor:
                    cursor.execute(query, (wallet_address, start_date, end_date))
                    rows = cursor.fetchall()

                    if not rows:
                        logger.info(f"No transaction data found for wallet {wallet_address}")
                        return None

                    total_invested = 0
                    total_taken_out = 0
                    unique_tokens = set()
                    tokens = []
                    token_addresses_to_fetch = set()

                    for row in rows:
                        token_address = row['tokenaddress']
                        token_name = row['token_name']
                        buy_token_change = float(row['buy_token_change'] or 0)
                        sell_token_change = float(row['sell_token_change'] or 0)
                        buy_usd_change = float(row['buy_usd_change'] or 0)
                        sell_usd_change = float(row['sell_usd_change'] or 0)
                        remaining_balance = buy_token_change - sell_token_change
                        token_realized_pnl = sell_usd_change - buy_usd_change

                        total_invested += buy_usd_change
                        total_taken_out += sell_usd_change
                        unique_tokens.add(token_address)

                        token = {
                            'tokenAddress': token_address,
                            'tokenName': token_name,
                            'totalInvested': buy_usd_change,
                            'totalTakenOut': sell_usd_change,
                            'buyTokenChange': buy_token_change,
                            'sellTokenChange': sell_token_change,
                            'buyUsdChange': buy_usd_change,
                            'sellUsdChange': sell_usd_change,
                            'remainingCoins': remaining_balance,
                            'remainingBalance': remaining_balance,
                            'realizedPnl': token_realized_pnl,
                            'currentPrice': 0,
                            'remainingValue': 0,
                            'totalPnl': token_realized_pnl,
                            'pnlPercentage': 0
                        }
                        tokens.append(token)
                        if remaining_balance > 0:
                            token_addresses_to_fetch.add(token_address)

                    # Fetch wallet info with normalized wallet address
                    cursor.execute(
                        "SELECT profitandloss, tradecount FROM smartmoneywallets WHERE TRIM(LOWER(walletaddress)) = ?",
                        (wallet_address,)
                    )
                    wallet_info = cursor.fetchone()
                    if wallet_info:
                        wallet_pnl = float(wallet_info['profitandloss'] or 0)
                        trade_count = int(wallet_info['tradecount'] or 0)
                    else:
                        logger.warning(f"No data found in smartmoneywallets for wallet {wallet_address}")
                        wallet_pnl = 0
                        trade_count = 0

                realized_pnl = total_taken_out - total_invested

                if token_addresses_to_fetch:
                    token_prices = self._fetch_token_prices(list(token_addresses_to_fetch)) or {}
                    for token in tokens:
                        token_address = token['tokenAddress']
                        token_price = token_prices.get(token_address)
                        if token_price and token['remainingBalance'] > 0:
                            price = token_price.price if token_price.marketCap > 10000 else 0
                            current_remaining_value = token['remainingBalance'] * price
                            if token_price and token_price.marketCap > current_remaining_value:
                                token['currentPrice'] = price
                                token['remainingValue'] = current_remaining_value
                            else:
                                token['currentPrice'] = 0
                                token['remainingValue'] = 0
                            token['totalPnl'] = token['realizedPnl'] + token['remainingValue']
                        
                        # Calculate PNL percentage
                        if token['totalInvested'] > 0:
                            token['pnlPercentage'] = (token['totalPnl'] / token['totalInvested']) * 100

                remaining_value = sum(token['remainingValue'] for token in tokens)
                total_pnl = realized_pnl + remaining_value

                end_time = time.time()
                # Calculate overall PNL percentage for wallet
                total_pnl_percentage = 0
                if total_invested > 0:
                    total_pnl_percentage = (total_pnl / total_invested) * 100
                
                # Sort tokens based on requested field
                valid_sort_fields = {
                    "tokenaddress": "tokenAddress",
                    "tokenname": "tokenName", 
                    "totalinvested": "totalInvested",
                    "totaltakenout": "totalTakenOut",
                    "remainingcoins": "remainingCoins",
                    "realizedpnl": "realizedPnl",
                    "totalpnl": "totalPnl",
                    "pnlpercentage": "pnlPercentage",
                    "remainingvalue": "remainingValue",
                    "currentprice": "currentPrice"
                }
                
                sort_field = valid_sort_fields.get(sort_by.lower(), "totalPnl")
                reverse_order = sort_order.lower() == "desc"
                
                try:
                    tokens = sorted(tokens, key=lambda x: x.get(sort_field, 0), reverse=reverse_order)
                except (KeyError, TypeError) as e:
                    logger.warning(f"Error sorting tokens by {sort_field}: {e}. Using default sort.")
                    tokens = sorted(tokens, key=lambda x: x.get("totalPnl", 0), reverse=True)
                
                result = {
                    'wallet': {
                        'walletAddress': wallet_address,
                        'totalInvested': total_invested,
                        'totalTakenOut': total_taken_out,
                        'totalRemainingValue': remaining_value,
                        'totalRealizedPnl': realized_pnl,
                        'totalPnl': total_pnl,
                        'totalPnlPercentage': total_pnl_percentage,
                        'uniqueTokenCount': len(unique_tokens),
                        'tradeCount': trade_count,
                        'walletPnl': wallet_pnl
                    },
                    'tokens': tokens,  # Include detailed token information
                    'period': {
                        'days': days,
                        'startDate': start_date.isoformat(),
                        'endDate': end_date.isoformat()
                    },
                    'metrics': {
                        'executionTimeSeconds': round(end_time - start_time, 2),
                        'tokenCount': len(unique_tokens)
                    }
                }
            
                return result

            except Exception as e:
                logger.error(f"Error getting wallet PNL details: {str(e)}")
                return None
        
        # Use cache manager for wallet report caching
        return cache_manager.get_report(cache_params, generate_wallet_report)
            
    def getTokenInvestorsPNL(self, token_id: str, days: int = 30, limit: int = 100, sortBy: str = "pnl", sortOrder: str = "desc", minTotalPnl: float = None, minWalletPnl: float = None) -> Dict[str, Any]:
        """
        Get PNL data for all wallets that have invested in a specific token.
        
        Args:
            token_id: The token ID/address to query
            days: Number of days to look back
            limit: Maximum number of wallets to return
            sortBy: Field to sort by (pnl, invested, tokens, trades)
            sortOrder: Sort order (asc or desc)
            minTotalPnl: Minimum total PNL filter
            minWalletPnl: Minimum wallet PNL filter
            
        Returns:
            Dictionary with wallet PNL metrics and token-specific data
        """
        # Cache key parameters
        cache_params = {
            "type": "token_investors",
            "token_id": token_id,
            "days": days,
            "limit": limit,
            "sortBy": sortBy,
            "sortOrder": sortOrder,
            "minTotalPnl": minTotalPnl,
            "minWalletPnl": minWalletPnl
        }
        
        def generate_token_report():
            """Internal function to generate fresh token investors report data."""
            try:
                start_time = time.time()
                logger.info(f"Starting token investors PNL report for token {token_id} over {days} days")
                
                start_date, end_date = self._get_date_range(days)
                sort_field, sort_order = self._get_sort_parameters(sortBy, sortOrder)
                
                # Get all wallet addresses that have invested in this token
                with self.conn_manager.transaction() as cursor:
                    # Get all wallet addresses that have invested in this token
                    cursor.execute("""
                        SELECT DISTINCT walletaddress 
                        FROM walletsinvested 
                        WHERE tokenid = ? AND status = 1
                    """, (token_id,))
                    
                    wallet_addresses = [row['walletaddress'] for row in cursor.fetchall()]
                    
                    if not wallet_addresses:
                        logger.info(f"No wallets found with investments in token {token_id}")
                        return {
                            'wallets': [],
                            'token': {'tokenId': token_id, 'tokenName': 'Unknown'},
                            'period': {
                                'days': days,
                                'startDate': start_date.isoformat(),
                                'endDate': end_date.isoformat()
                            },
                            'metrics': {
                                'executionTimeSeconds': 0,
                                'walletCount': 0
                            }
                        }
                    
                    # We'll get the token name from the query results
                    token_name = 'Unknown'  # Default value, will be updated when processing results
                    
                    # Create placeholders for SQL IN clause
                    placeholders = ','.join(['?' for _ in wallet_addresses])
                    
                    # Optimized query to get all transaction data for these wallets with pre-filtering
                    query = f"""
                    SELECT 
                        walletaddress,
                        tokenaddress,
                        COALESCE(MAX(buytokenname), MAX(selltokenname), 'Unknown') AS token_name,
                        SUM(buytokenchange) AS total_buytoken,
                        SUM(selltokenchange) AS total_selltoken,
                        SUM(buyusdchange) AS total_buyusd,
                        SUM(sellusdchange) AS total_sellusd
                    FROM 
                        smartmoneymovements
                    WHERE 
                        walletaddress IN ({placeholders})
                        AND date >= ? AND date <= ?
                        AND tokenaddress NOT IN {SQL_EXCLUDED_TOKENS}
                        AND (buyusdchange > 0 OR sellusdchange > 0)
                    GROUP BY 
                        walletaddress, tokenaddress
                    HAVING 
                        (SUM(buyusdchange) > 0 OR SUM(sellusdchange) > 0)
                    """
                    
                    params = wallet_addresses + [start_date, end_date]
                    cursor.execute(query, params)
                    results = cursor.fetchall()
                    
                    # Process transaction data
                    wallet_data = {}
                    
                    # Process transaction data
                    for row in results:
                        wallet_address = row['walletaddress']
                        token_address = row['tokenaddress']
                        total_buytoken = float(row['total_buytoken'] or 0)
                        total_selltoken = float(row['total_selltoken'] or 0)
                        total_buyusd = float(row['total_buyusd'] or 0)
                        total_sellusd = float(row['total_sellusd'] or 0)
                        remaining_balance = total_buytoken - total_selltoken
                        
                        # CRITICAL FIX: Only include tokens where there was actual investment in the time range
                        # Skip tokens with zero buyusdchange (bought before period but sold during period)
                        if total_buyusd <= 0:
                            continue
                        
                        if wallet_address not in wallet_data:
                            wallet_data[wallet_address] = {
                                'total_invested': 0,
                                'total_taken_out': 0,
                                'unique_tokens': set(),
                                'token_balances': {},
                                'tokens': []
                            }
                        
                        wallet = wallet_data[wallet_address]
                        wallet['total_invested'] += total_buyusd
                        wallet['total_taken_out'] += total_sellusd
                        wallet['unique_tokens'].add(token_address)
                        
                        if remaining_balance > 0:
                            wallet['token_balances'][token_address] = remaining_balance
                        
                        # Create token detail entry
                        token_realized_pnl = total_sellusd - total_buyusd
                        token_name = row['token_name'] or 'Unknown'
                        
                        token_detail = {
                            'tokenAddress': token_address,
                            'tokenName': token_name,
                            'buyTokenChange': total_buytoken,
                            'sellTokenChange': total_selltoken,
                            'buyUsdChange': total_buyusd,
                            'sellUsdChange': total_sellusd,
                            'remainingBalance': remaining_balance,
                            'realizedPnl': token_realized_pnl,
                            'currentPrice': 0,
                            'remainingValue': 0,
                            'totalPnl': token_realized_pnl
                        }
                        
                        wallet['tokens'].append(token_detail)
                    
                    # Build wallet list with PNL data
                    wallets = []
                    for wallet_address, data in wallet_data.items():
                        # Only include wallets that have actual investments (total_invested > 0)
                        # This fixes the PNL calculation bug where tokens bought before the time period
                        # but sold within it would show incorrect positive PNL
                        if data['total_invested'] > 0 and (token_id in data['token_balances'] or any(token == token_id for token in data['unique_tokens'])):
                            realized_pnl = data['total_taken_out'] - data['total_invested']
                            wallets.append({
                                'walletAddress': wallet_address,
                                'totalInvested': data['total_invested'],
                                'totalTakenOut': data['total_taken_out'],
                                'uniqueTokenCount': len(data['unique_tokens']),
                                'realizedPnl': realized_pnl,
                                'tokenBalances': data['token_balances'],
                                'remainingValue': 0,
                                'totalPnl': realized_pnl,
                                'tradeCount': 0,
                                'walletPnl': 0,
                                'tokens': data['tokens']
                            })
                    
                    # Get wallet PNL and trade count data
                    if wallets:
                        wallet_addresses_list = [w['walletAddress'] for w in wallets]
                        placeholders = ','.join(['?' for _ in wallet_addresses_list])
                        
                        wallet_info_query = f"""
                        SELECT walletaddress, profitandloss, tradecount
                        FROM smartmoneywallets
                        WHERE walletaddress IN ({placeholders})
                        """
                        cursor.execute(wallet_info_query, wallet_addresses_list)
                        wallet_info = {row['walletaddress']: row for row in cursor.fetchall()}
                                
                        for wallet in wallets:
                            info = wallet_info.get(wallet['walletAddress'], {}) 
                            if not info:
                                logger.warning(f"No data found in smartmoneywallets for wallet {wallet['walletAddress']}")
                            try:
                                wallet['walletPnl'] = float(info['profitandloss'])
                            except ValueError:
                                logger.info(f"Invalid profitandloss value for wallet {wallet['walletAddress']}: {info.get('profitandloss')}")
                                wallet['walletPnl'] = 0
                                
                            try:
                                wallet['tradeCount'] = int(info['tradecount'])
                            except ValueError:
                                logger.info(f"Invalid tradecount value for wallet {wallet['walletAddress']}: {info.get('tradecount')}")
                                wallet['tradeCount'] = 0
                    
                    # Apply wallet PNL filter if specified
                    if minWalletPnl is not None and minWalletPnl > 0:
                        wallets = [w for w in wallets if w['walletPnl'] >= minWalletPnl]
                    
                    # Optimize token price fetching by only getting prices for tokens with balances
                    all_token_addresses = set()
                    for wallet in wallets:
                        all_token_addresses.update(wallet['tokenBalances'].keys())
                    
                    # Batch token price fetching with error handling
                    token_prices = {}
                    if all_token_addresses:
                        try:
                            token_prices = self._fetch_token_prices(list(all_token_addresses))
                        except Exception as e:
                            logger.warning(f"Failed to fetch token prices, continuing without prices: {str(e)}")
                            token_prices = {}
                    
                    for wallet in wallets:
                        remaining_value = 0
                        
                        # Update token prices and values for all tokens in the wallet
                        for token_detail in wallet['tokens']:
                            token_address = token_detail['tokenAddress']
                            token_price = token_prices.get(token_address)
                            price = token_price.price if token_price and token_price.marketCap > 10000 else 0
                            token_detail['currentPrice'] = price
                            
                            # Calculate remaining value if there's a balance
                            if token_detail['remainingBalance'] > 0:
                                current_remaining_value = token_detail['remainingBalance'] * price
                                if token_price and token_price.marketCap > current_remaining_value:
                                    token_detail['remainingValue'] = current_remaining_value
                                else:
                                    token_detail['currentPrice'] = 0
                                    token_detail['remainingValue'] = 0
                                token_detail['totalPnl'] = token_detail['realizedPnl'] + token_detail['remainingValue']
                                remaining_value += token_detail['remainingValue']
                        
                        wallet['remainingValue'] = remaining_value
                        wallet['totalPnl'] = wallet['realizedPnl'] + remaining_value
                    
                    # Apply total PNL filter if specified
                    if minTotalPnl is not None and minTotalPnl > 0:
                        wallets = [w for w in wallets if w['totalPnl'] >= minTotalPnl]
                    
                    # Sort and limit results
                    wallets.sort(key=lambda x: x[sort_field], reverse=(sort_order == "desc"))
                    wallets = wallets[:limit]
                
                end_time = time.time()
                execution_time = end_time - start_time
                logger.info(f"Token investors PNL report generated in {execution_time:.2f} seconds")
                
                result = {
                    'wallets': wallets,
                    'token': {
                        'tokenId': token_id,
                        'tokenName': token_name,
                        'currentPrice': token_prices.get(token_id).price if token_id in token_prices else None
                    },
                    'period': {
                        'days': days,
                        'startDate': start_date.isoformat(),
                        'endDate': end_date.isoformat()
                    },
                    'metrics': {
                        'executionTimeSeconds': round(execution_time, 2),
                        'walletCount': len(wallets),
                        'tokenCount': len(all_token_addresses)
                    }
                }
                
                return result
                
            except Exception as e:
                logger.error(f"Error generating token investors PNL report: {str(e)}")
                return {
                    'wallets': [],
                    'token': {'tokenId': token_id, 'tokenName': 'Unknown'},
                    'period': {
                        'days': days,
                        'startDate': datetime.now().date().isoformat(),
                        'endDate': datetime.now().date().isoformat()
                    },
                    'metrics': {
                        'executionTimeSeconds': 0,
                        'walletCount': 0
                    },
                    'error': str(e)
                }
        
        # Use cache manager for token investors report caching
        return cache_manager.get_report(cache_params, generate_token_report)
        
def format_query(query, params):
    # Split the query by the placeholder '?'
    parts = query.split('?')
    
    # Check if the number of placeholders matches the number of parameters
    if len(parts) - 1 != len(params):
        raise ValueError("Number of placeholders does not match number of parameters")
    
    # Start with the first part of the query
    formatted_query = parts[0]
    
    # Iterate through parameters and corresponding query parts
    for i, param in enumerate(params):
        if param is None:
            # Handle NULL values
            formatted_param = 'NULL'
        elif isinstance(param, str):
            # Handle strings: enclose in single quotes and escape existing quotes
            formatted_param = "'" + param.replace("'", "''") + "'"
        else:
            # Handle numbers and other types by converting to string
            formatted_param = str(param)
        # Append the formatted parameter and the next part of the query
        formatted_query += formatted_param + parts[i + 1]
    
    return formatted_query