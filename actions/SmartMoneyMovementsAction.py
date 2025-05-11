from typing import Optional, Dict, List, DefaultDict, Tuple
from datetime import datetime, timedelta
import time
from decimal import Decimal
from collections import defaultdict
from logs.logger import get_logger
from database.operations.sqlite_handler import SQLitePortfolioDB
from services.CieloServiceHandler import CieloServiceHandler
from database.smartmoneymovements.SmartMoneyMovementsHandler import SmartMoneyMovementsHandler


logger = get_logger(__name__)

class SmartMoneyMovementsAction:
    """Handles smart money movements analysis workflow"""
    
    def __init__(self, db: SQLitePortfolioDB):
        """Initialize action with database and service instances"""
        self.db = db
        self.cielo_service = CieloServiceHandler(db)
        self.smartMoneyMovementsHandler = SmartMoneyMovementsHandler(db.conn_manager)

    def processWalletMovements(self, walletAddress: str) -> bool:
        """
        Process and store movements for a specific wallet
        
        Args:
            wallet_address: Wallet address to process
            
        Returns:
            bool: Success status
        """
        start_time = time.time()
        try:
            # Get last fetch time
            lastFetchedTime = self.smartMoneyMovementsHandler.getLastFetchedTime(walletAddress)
            current_time = int(datetime.now().timestamp())
            
            # If lastFetchedTime is null or empty, set it to 90 days ago
            if lastFetchedTime is None:
                lastFetchedTime = int((datetime.now() - timedelta(days=90)).timestamp())
            
            # Get all transactions since last fetch
            transactions = self.getAllTransactions(walletAddress, lastFetchedTime, current_time)
            if not transactions:
                logger.info(f"No new transactions found for wallet {walletAddress}")
                return True
                
            # Group and process transactions
            movements = self.processTransactions(transactions)
            
            # Prepare batch data for database operations
            batch_data = self.prepareBatchData(walletAddress, movements)
            
            # Store movements and update last fetch time
            self.smartMoneyMovementsHandler.storeMovementsBatch(batch_data)
            self.smartMoneyMovementsHandler.updateLastFetchedTime(walletAddress)
            
            executionTime = time.time() - start_time
            logger.info(f"Successfully processed movements for {walletAddress} in {executionTime:.2f} seconds")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process movements for {walletAddress}: {str(e)}")
            executionTime = time.time() - start_time
            logger.error(f"Action failed after {executionTime:.2f} seconds")
            return False

    def getAllTransactions(self, walletAddress: str, fromTimestamp: Optional[int], 
                            toTimestamp: int) -> Optional[List[Dict]]:
        """
        Get all transactions for a wallet within a time period
        
        Args:
            wallet_address: Wallet address to query
            from_timestamp: Start timestamp (None for first run)
            to_timestamp: End timestamp
            
        Returns:
            Optional[List[Dict]]: List of transactions or None if failed
        """
        allTransactions = []
        startFrom = None
        
        while True:
            api_key_data = self.db.credentials.getNextValidApiKey(
                serviceName=self.cielo_service.service.service_name,
                requiredCredits=self.cielo_service.creditsPerCall
            )
            if not api_key_data:
                logger.error("No valid API key available")
                return None
                
            # Get page of transactions
            result = self.getTransactionsPage(
                api_key=api_key_data['apikey'],
                walletAddress=walletAddress,
                fromTimestamp=fromTimestamp,
                toTimestamp=toTimestamp,
                startFrom=startFrom
            )
            
            if not result:
                break
                
            # Unpack response
            items = result.get('data', {}).get('items', [])
            paging = result.get('data', {}).get('paging', {})
            
            # Update API key credits
            self.db.credentials.deductAPIKeyCredits(api_key_data['id'], self.cielo_service.creditsPerCall)
            
            # Add transactions to list
            allTransactions.extend(items)
            
            # Check if more pages exist
            has_next_page = paging.get('has_next_page', False)
            if not has_next_page:
                break
                
            # Get next cursor for pagination
            startFrom = paging.get('next_cursor')
            time.sleep(1)  # Rate limiting
            
        return allTransactions

    def getTransactionsPage(self, api_key: str, walletAddress: str, 
                             fromTimestamp: Optional[int], toTimestamp: int,
                             startFrom: Optional[str] = None) -> Optional[Dict]:
        """
        Get single page of transactions
        
        Args:
            api_key: Valid Cielo API key
            wallet_address: Wallet address to analyze
            from_timestamp: Start timestamp
            to_timestamp: End timestamp
            start_from: Pagination cursor
            
        Returns:
            Optional[Dict]: Raw API response or None if failed
        """
        params = {
            'wallet': walletAddress,
            'limit': 100,
            'chains': '',
            'txTypes': 'swap',
            'minUSD': 10,
            'toTimestamp': toTimestamp
        }
        
        if fromTimestamp:
            params['fromTimestamp'] = fromTimestamp
            
        if startFrom:
            params['startFrom'] = startFrom
            
        headers = {'accept': 'application/json', 'x-api-key': api_key}
        
        try:
            response = self.cielo_service.session.get(
                f"{self.cielo_service.baseUrl}/feed",
                headers=headers,
                params=params,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get('status') == 'ok':
                return data
                
        except Exception as e:
            logger.error(f"Failed to get transactions page: {e}")
            
        return None

    def processTransactions(self, transactions: List[Dict]) -> Dict[str, Dict[str, Dict]]:
        """
        Process transactions and group by token and date.
        Token0 is always the token being sold, Token1 is always the token being bought.
        
        Args:
            transactions: List of transactions to process
            
        Returns:
            Dict[str, Dict[str, Dict]]: Processed movements grouped by token and date
        """
        # Use defaultdict for cleaner initialization
        movements: DefaultDict = defaultdict(
            lambda: defaultdict(
                lambda: {
                    'buytokenchange': Decimal('0'),
                    'selltokenchange': Decimal('0'),
                    'buyusdchange': Decimal('0'),
                    'sellusdchange': Decimal('0'),
                    'buytokenname': None,
                    'selltokenname': None
                }
            )
        )
        
        for tx in transactions:
            try:
                # Convert timestamp to date
                tx_date = datetime.fromtimestamp(tx['timestamp']).date()
                date_str = tx_date.isoformat()
                
                # Get token addresses
                token0_address = tx['token0_address']  # Token being sold
                token1_address = tx['token1_address']  # Token being bought
                
                # Get token names/symbols
                token0_symbol = tx.get('token0_symbol', '')
                token1_symbol = tx.get('token1_symbol', '')
                
                # Process token0 (sold token)
                movements[token0_address][date_str]['selltokenchange'] += Decimal(str(tx['token0_amount']))
                movements[token0_address][date_str]['sellusdchange'] += Decimal(str(tx['token0_amount_usd']))
                if token0_symbol and not movements[token0_address][date_str]['selltokenname']:
                    movements[token0_address][date_str]['selltokenname'] = token0_symbol
                
                # Process token1 (bought token)
                movements[token1_address][date_str]['buytokenchange'] += Decimal(str(tx['token1_amount']))
                movements[token1_address][date_str]['buyusdchange'] += Decimal(str(tx['token1_amount_usd']))
                if token1_symbol and not movements[token1_address][date_str]['buytokenname']:
                    movements[token1_address][date_str]['buytokenname'] = token1_symbol
                    
            except Exception as e:
                logger.error(f"Failed to process transaction: {e}")
                continue
                
        return dict(movements)  # Convert back to regular dict for return

    def prepareBatchData(self, wallet_address: str, movements: Dict[str, Dict[str, Dict]]) -> List[Tuple]:
        """
        Prepare batch data for database operations
        
        Args:
            wallet_address: Wallet address
            movements: Processed movements
            
        Returns:
            List[Tuple]: Prepared batch data for database operations
        """
        batch_data = []
        for token_address, date_movements in movements.items():
            for date_str, movement_data in date_movements.items():
                date = datetime.fromisoformat(date_str).date()
                batch_data.append((
                    wallet_address,
                    token_address,
                    float(movement_data['buytokenchange']),
                    float(movement_data['selltokenchange']),
                    float(movement_data['buyusdchange']),
                    float(movement_data['sellusdchange']),
                    movement_data['buytokenname'],
                    movement_data['selltokenname'],
                    date
                ))
        return batch_data 