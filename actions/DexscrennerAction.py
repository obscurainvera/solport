"""
Fetches token price information from DexScreener API and returns price details for
the Raydium pool
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import requests
from datetime import datetime
from decimal import Decimal
from logs.logger import get_logger

logger = get_logger(__name__)

@dataclass
class TokenPrice:
    """Data class to store token price information"""
    price: float  # priceUsd
    fdv: float   # fdv (Fully Diluted Valuation)
    marketCap: float  # marketCap
    name: str    # token name
    symbol: str  # token symbol
    tokenAge: int = 0  # token age in days

class DexScreenerAction:
    """Handles DexScreener API request workflow"""
    
    def __init__(self):
        """Initialize action with base URL"""
        self.baseUrl = "https://api.dexscreener.com/latest/dex/tokens"

    def makeRequest(self, tokenAddress: str) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to DexScreener API
        
        Args:
            tokenAddress: Token address to query
            
        Returns:
            API response as dictionary or None if request failed
        """
        try:
            url = f"{self.baseUrl}/{tokenAddress}"
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    def makeBatchRequest(self, tokenAddresses: List[str], chainId: str = "solana") -> Optional[List[Dict[str, Any]]]:
        """
        Make batch HTTP request to DexScreener API for multiple tokens
        
        Args:
            tokenAddresses: List of token addresses to query
            chainId: Chain ID (default: solana)
            
        Returns:
            API response as list of dictionaries or None if request failed
        """
        if not tokenAddresses:
            logger.warning("No token addresses provided for batch request")
            return []
            
        try:
            # The new API endpoint for batch requests
            tokenAddressesStr = ','.join(tokenAddresses)
            batchUrl = f"https://api.dexscreener.com/tokens/v1/{chainId}/{tokenAddressesStr}"
            
            logger.info(f"Making batch request to {batchUrl}")
            
            response = requests.get(batchUrl, timeout=30)  # Add timeout
            
            if response.status_code != 200:
                logger.error(f"Batch API request failed with status code {response.status_code}: {response.text}")
                return None
                
            responseData = response.json()
            
            if not isinstance(responseData, list):
                logger.error(f"Unexpected response format: {responseData}")
                return None
                
            logger.info(f"Successfully received data for {len(responseData)} pairs")
            return responseData
            
        except requests.exceptions.Timeout:
            logger.error("Batch API request timed out")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Batch API request failed: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in batch API request: {str(e)}")
            return None

    def parseResponseForRaydium(self, pairs: List[Dict[str, Any]]) -> Optional[TokenPrice]:
        """
        Parse response to find Raydium or Pumpswap pool data
        
        Args:
            pairs: List of pairs from API response
            
        Returns:
            TokenPrice object with price information or None if not found
        """
        try:
            # Find Raydium or Pumpswap pairs with highest liquidity
            validPairs = [
                pair for pair in pairs 
                if pair.get('dexId') in ['raydium', 'pumpswap'] and 
                pair.get('quoteToken', {}).get('symbol') in ['USDC', 'SOL']
            ]
            
            if not validPairs:
                logger.warning("No Raydium or Pumpswap pairs found")
                return None
                
            # Sort by liquidity and get the highest liquidity pair
            highestLiquidityPair = max(
                validPairs, 
                key=lambda x: float(x.get('liquidity', {}).get('usd', 0))
            )
            
            logger.info(f"Selected {highestLiquidityPair.get('dexId')} pair with highest liquidity: {highestLiquidityPair.get('liquidity', {}).get('usd', 0)} USD")
            
            baseToken = highestLiquidityPair.get('baseToken', {})
            
            # Calculate token age from pairCreatedAt
            tokenAge = 0  # Default value
            if 'pairCreatedAt' in highestLiquidityPair:
                createdAtMs = highestLiquidityPair['pairCreatedAt']
                createdAt = datetime.fromtimestamp(createdAtMs / 1000)  # Convert ms to seconds
                now = datetime.now()
                tokenAge = (now - createdAt).days
                logger.info(f"Token age calculated: {tokenAge} days (created at {createdAt})")
            
            return TokenPrice(
                price=float(highestLiquidityPair['priceUsd']),
                fdv=float(highestLiquidityPair['fdv']),
                marketCap=float(highestLiquidityPair['marketCap']),
                name=baseToken.get('name', ''),
                symbol=baseToken.get('symbol', ''),
                tokenAge=tokenAge
            )
            
        except Exception as e:
            logger.error(f"Failed to parse response: {str(e)}")
            return None

    def getTokenPrice(self, tokenAddress: str) -> Optional[TokenPrice]:
        """
        Get token price from DexScreener
        
        Args:
            tokenAddress: Token address to query
            
        Returns:
            TokenPrice object with price information or None if not found
        """
        try:
            response = self.makeRequest(tokenAddress)
            if not response or 'pairs' not in response or not response['pairs']:
                return None
                
            # Parse response to find Raydium pool data
            return self.parseResponseForRaydium(response['pairs'])
        except Exception as e:
            logger.error(f"Failed to get token price: {str(e)}")
            return None

    def getBatchTokenPrices(self, tokenAddresses: List[str], chainId: str = "solana") -> Dict[str, Optional[TokenPrice]]:
        """
        Get token prices for multiple tokens in batches
        
        Args:
            tokenAddresses: List of token addresses to query
            chainId: Chain ID (default: solana)
            
        Returns:
            Dictionary mapping token addresses to TokenPrice objects
        """
        result = {}
        
        if not tokenAddresses:
            logger.warning("No token addresses provided for batch price fetching")
            return result
            
        logger.info(f"Fetching prices for {len(tokenAddresses)} tokens in batches of 30")
        
        # Process in batches of 30 tokens (API limit)
        for i in range(0, len(tokenAddresses), 30):
            batch = tokenAddresses[i:i+30]
            batchSize = len(batch)
            
            logger.info(f"Processing batch {i//30 + 1} with {batchSize} tokens")
            
            try:
                response = self.makeBatchRequest(batch, chainId)
                
                if not response:
                    logger.error(f"Batch request failed for {batchSize} tokens")
                    # If batch request fails, mark all tokens in this batch as None
                    for tokenAddress in batch:
                        result[tokenAddress] = None
                    continue
                
                # Process each token in the response
                processedTokens = set()
                for pairData in response:
                    if not pairData or 'baseToken' not in pairData:
                        continue
                        
                    tokenAddress = pairData['baseToken']['address']
                    processedTokens.add(tokenAddress)
                    
                    # Create TokenPrice object from the pair data
                    price = float(pairData.get('priceUsd', 0))
                    fdv = float(pairData.get('fdv', 0))
                    marketCap = float(pairData.get('marketCap', 0))
                    
                    # Calculate token age from pairCreatedAt
                    tokenAge = 0  # Default value
                    if 'pairCreatedAt' in pairData:
                        createdAtMs = pairData['pairCreatedAt']
                        createdAt = datetime.fromtimestamp(createdAtMs / 1000)  # Convert ms to seconds
                        now = datetime.now()
                        tokenAge = (now - createdAt).days
                    
                    result[tokenAddress] = TokenPrice(
                        price=price,
                        fdv=fdv,
                        marketCap=marketCap,
                        name=pairData.get('baseToken', {}).get('name', ''),
                        symbol=pairData.get('baseToken', {}).get('symbol', ''),
                        tokenAge=tokenAge
                    )
                
                # Check for missing tokens in the response
                tokensNotFound = set(batch) - processedTokens
                if tokensNotFound:
                    logger.warning(f"Missing price data for {len(tokensNotFound)} tokens in batch")
                    for tokenAddress in tokensNotFound:
                        result[tokenAddress] = None
                        
                logger.info(f"Successfully processed batch with {len(processedTokens)} tokens")
                
            except Exception as e:
                logger.error(f"Failed to process batch token prices: {str(e)}")
                # Mark all tokens in this batch as None on error
                for tokenAddress in batch:
                    if tokenAddress not in result:
                        result[tokenAddress] = None
        
        logger.info(f"Completed fetching prices for {len(tokenAddresses)} tokens, found data for {sum(1 for v in result.values() if v is not None)} tokens")
        return result 