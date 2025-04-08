"Takes all the wallets invested in a specific token and persists them to the database"

from typing import Optional, Dict, Any, List
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.operations.schema import WalletsInvested, WalletInvestedStatusEnum
import requests
from datetime import datetime
import time
import parsers.WalletsInvestedParser as WalletsInvestedParser
from logs.logger import get_logger
import re
from decimal import Decimal
logger = get_logger(__name__)

class WalletsInvestedAction:
    """Handles complete token analysis request workflow"""
    
    def __init__(self, db: SQLitePortfolioDB):
        """
        Initialize action with required security parameters
        Args:
            db: Database handler for authentication
        """
        self.db = db
        self.session = requests.Session()
        self._configure_headers()
        self.timeout = 30
        self.max_retries = 3
        self.api_url = 'https://app.chainedge.io/token_holdings_solana_table_sql/'
        self.token_wallet_list_api_url = 'https://app.chainedge.io/tokenWalletList/'

    def _configure_headers(self):
        """Set headers from endpoint configuration"""
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://app.chainedge.io',
            'Priority': 'u=1, i',
            'Referer': 'https://app.chainedge.io/solana/',
            'Sec-Ch-Ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
            'X-Requested-With': 'XMLHttpRequest'
        }

    def buildPayload(self, token_id: str) -> Dict[str, str]:
        """
        Construct payload with token ID
        
        Args:
            token_id (str): Token ID to analyze
        """
        return {
            'token_id': token_id,
            'pageType': 'TokenPageL2'
        }
        

    def fetchWalletsInvestedForNewToken(self, cookie: str, tokenId: str, portsummaryId: int) -> Optional[List[WalletsInvested]]:
        """
        Fetch wallets for new tokens (age <= 1 day) using the alternative API
        
        Args:
            cookie (str): Authentication cookie
            tokenId (str): Token ID 
            portsummaryId (int): Portfolio summary ID
            
        Returns:
            Optional[List[WalletsInvested]]: List of wallet objects or None if failed
        """
        try:
            logger.info(f"Using alternative API for new token {tokenId}")
            
            # Make request to alternative API
            response = self.session.get(
                f"{self.token_wallet_list_api_url}?token_id={tokenId}",
                headers={**self.headers, 'Cookie': cookie},
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            if not response.content:
                raise ValueError("Empty response received")
                
            data = response.json()
            
            if not data or 'data' not in data or not data['data']:
                logger.warning(f"No wallet data found for new token {tokenId}")
                return None
                
            # Use the parser to convert the response to WalletsInvested objects
            parsedItems = WalletsInvestedParser.parseWalletsInvestedAPIResponseForNewTokens(
                data,
                portsummaryId, 
                tokenId
            )
            
            if not parsedItems:
                logger.warning(f"No wallets parsed for new token {tokenId}")
                return None
                
            logger.info(f"Found {len(parsedItems)} wallets for new token {tokenId}")
            return parsedItems
            
        except Exception as e:
            logger.error(f"Failed to fetch wallets for new token {tokenId}: {str(e)}")
            return None

    def fetchAndPersistWalletsInvestedInASpecificToken(self, cookie: str, tokenId: str, portsummaryId: int, tokenAge: Decimal) -> Optional[Dict[str, Any]]:
        """Execute token analysis request with retry on failure"""
        startTime = time.time()
        try:
             
            # Use different API for new tokens (age <= 1 day)
            if tokenAge <= 1:
                parsedItems = self.fetchWalletsInvestedForNewToken(cookie, tokenId, portsummaryId)
            else:
                # Use the regular API for older tokens
                payload = self.buildPayload(tokenId)
                response = self.session.post(
                    self.api_url,
                    headers={**self.headers, 'Cookie': cookie},
                    data=payload,
                    timeout=self.timeout
                )
                
                response.raise_for_status()
                
                if not response.content:
                    raise ValueError("Empty response received")

                parsedItems = WalletsInvestedParser.parseWalletsInvestedInASpecificTokenAPIResponse(
                    response.json(), 
                    portsummaryId,
                    tokenId
                )
            
            if parsedItems:
                self.persistWalletsInvestedData(parsedItems)
                
                # Get current active wallets from the database for this token
                investedWallets = self.db.walletsInvested.getActiveWalletsByTokenId(tokenId)
                
                # Extract wallet addresses from the parsed API response
                updatedInvestedWalletsList = {item.walletaddress for item in parsedItems}
                
                # Mark missing wallets as inactive
                walletsToInactivate = []
                for walletAddress in investedWallets:
                    if walletAddress not in updatedInvestedWalletsList:
                        walletsToInactivate.append(walletAddress)
                
                if walletsToInactivate:
                    logger.info(f"Marking {len(walletsToInactivate)} wallets as inactive for token {tokenId}")
                    self.db.walletsInvested.markWalletsAsInactive(tokenId, walletsToInactivate)
            
                logger.debug(f"Successfully processed token analysis for {tokenId}")
                executionTime = time.time() - startTime
                logger.debug(f"Action completed in {executionTime:.2f} seconds for token {tokenId}")
                return parsedItems
            else:
                logger.warning(f"No valid analysis data for token {tokenId}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to execute token analysis: {str(e)}")
            return None

    def persistWalletsInvestedData(self, items: List[WalletsInvested]):
        """
        Persist token analysis to database and maintain history.
        """
        try:
            with self.db.transaction() as cursor:
                for item in items:
                    # Get existing record
                    cursor.execute("""
                        SELECT * FROM walletsinvested 
                        WHERE tokenid = ? AND walletaddress = ?
                    """, (item.tokenid, item.walletaddress))
                    existing = cursor.fetchone()

                    if existing:
                        # Check if any relevant fields have changed
                        fieldsToCompare = [
                            ('coinquantity', float(item.coinquantity), float(existing['coinquantity']) if existing['coinquantity'] else 0)
                        ]
                        
                        # Log field values for debugging
                        for field, newVal, oldVal in fieldsToCompare:
                            logger.debug(f"Field {field}: old={oldVal}, new={newVal}, diff={abs(newVal - oldVal)}")
                        
                        hasChanges = any(
                            abs(newVal - oldVal) > 1e-10
                            for field, newVal, oldVal in fieldsToCompare
                        )

                        if hasChanges or existing['status'] != WalletInvestedStatusEnum.ACTIVE.value:
                            logger.debug(f"Changes detected for wallet {item.walletaddress} and token {item.tokenid}")
                            
                            # Pass the sqlite3.Row object directly
                            self.db.walletsInvested.insertWalletHistory(existing, cursor)
                            update_success = self.db.walletsInvested.updateWalletsInvested(item, cursor)
                            if update_success:
                                logger.info(f"Updated wallet {item.walletaddress} for token {item.tokenid} and recorded history")
                            else:
                                logger.error(f"Failed to update wallet {item.walletaddress} for token {item.tokenid}")
                    else:
                        # Insert new record
                        self.db.walletsInvested.insertWalletInvested(item, cursor)
                        logger.info(f"Inserted new wallet {item.walletaddress} for token {item.tokenid}")

        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise 