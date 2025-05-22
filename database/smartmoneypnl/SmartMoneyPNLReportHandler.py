from typing import Dict, List, Any, Tuple
from database.operations.base_handler import BaseSQLiteHandler
from logs.logger import get_logger
from datetime import datetime, timedelta
from actions.DexscrennerAction import DexScreenerAction
import time
from tenacity import retry, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

# Configurable excluded token IDs (can be loaded from config file or database in production)
EXCLUDED_TOKEN_IDS = [
    "native",
    "So11111111111111111111111111111111111111112",  # Wrapped SOL
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC
]
SQL_EXCLUDED_TOKENS = "(" + ",".join([f"'{token}'" for token in EXCLUDED_TOKEN_IDS]) + ")"

class SmartMoneyPNLReportHandler(BaseSQLiteHandler):
    def __init__(self, conn_manager):
        super().__init__(conn_manager)
        self.dex_screener = DexScreenerAction()

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
        """Fetch token prices with retry logic."""
        try:
            return self.dex_screener.getBatchTokenPrices(token_addresses)
        except Exception as e:
            logger.error(f"Failed to fetch token prices: {str(e)}")
            raise

    def getTopPNLWallets(self, days: int = 30, limit: int = 100, sortBy: str = "pnl", sortOrder: str = "desc", minTotalPnl: float = None, minWalletPnl: float = None) -> Dict[str, Any]:
        """
        Get top PNL wallets for the specified period with optimized data fetching and processing.

        Args:
            days: Number of days to look back.
            limit: Maximum number of wallets to return.
            sortBy: Field to sort by (pnl, invested, tokens, trades).
            sortOrder: Sort order (asc or desc).
            minTotalPnl: Minimum total PNL filter.
            minWalletPnl: Minimum wallet PNL filter.

        Returns:
            Dictionary with wallet PNL metrics and metadata.
        """
        try:
            start_time = time.time()
            logger.info(f"Starting top PNL wallets report generation for {days} days")
            
            start_date, end_date = self._get_date_range(days)
            sort_field, sort_order = self._get_sort_parameters(sortBy, sortOrder)

            # Single query to fetch all necessary transaction data with normalized wallet addresses
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
            GROUP BY 
                walletaddress, tokenaddress
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
                    wallet_info_query = f"""
                    SELECT walletaddress , profitandloss, tradecount
                    FROM smartmoneywallets
                    """
                    cursor.execute(wallet_info_query)
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

                all_token_addresses = set()
                for wallet in wallets: #add all token addresses that a certain wallet has some balance of
                    all_token_addresses.update(wallet['tokenBalances'].keys())

                token_prices = self._fetch_token_prices(list(all_token_addresses)) if all_token_addresses else {}

                for wallet in wallets:
                    remaining_value = 0
                    for token, balance in wallet['tokenBalances'].items():
                        token_price = token_prices.get(token)
                        price = token_price.price if token_price else 0
                        remaining_value += balance * price
                    wallet['remainingValue'] = remaining_value
                    wallet['totalPnl'] = wallet['realizedPnl'] + remaining_value

                if minTotalPnl is not None and minTotalPnl > 0:
                    wallets = [w for w in wallets if w['totalPnl'] >= minTotalPnl]

                wallets.sort(key=lambda x: x[sort_field], reverse=(sort_order == "desc"))
                wallets = wallets[:limit]

            end_time = time.time()
            logger.info(f"Report generated in {end_time - start_time:.2f} seconds")

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
                    'tokenCount': len(all_token_addresses)
                }
            }

        except Exception as e:
            logger.error(f"Error generating PNL report: {str(e)}")
            return {
                'wallets': [],
                'period': {'days': days, 'startDate': '', 'endDate': datetime.now().date().isoformat()},
                'error': str(e)
            }

    def getWalletPNLDetails(self, wallet_address: str, days: int = 30) -> Dict[str, Any]:
        """
        Get detailed PNL information for a specific wallet, including token-level breakdown.

        Args:
            wallet_address: Wallet address to analyze.
            days: Number of days to look back.

        Returns:
            Dictionary with detailed wallet PNL data, including token details.
        """
        try:
            start_time = time.time()
            start_date, end_date = self._get_date_range(days)

            # Normalize input wallet address
            wallet_address = wallet_address.strip().lower()

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
                        price = token_price.price
                        token['currentPrice'] = price
                        token['remainingValue'] = token['remainingBalance'] * price
                        token['totalPnl'] = token['realizedPnl'] + token['remainingValue']

            remaining_value = sum(token['remainingValue'] for token in tokens)
            total_pnl = realized_pnl + remaining_value

            end_time = time.time()
            return {
                'wallet': {
                    'walletAddress': wallet_address,
                    'totalInvested': total_invested,
                    'totalTakenOut': total_taken_out,
                    'uniqueTokenCount': len(unique_tokens),
                    'realizedPnl': realized_pnl,
                    'remainingValue': remaining_value,
                    'totalPnl': total_pnl,
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

        except Exception as e:
            logger.error(f"Error getting wallet PNL details: {str(e)}")
            return None
        
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