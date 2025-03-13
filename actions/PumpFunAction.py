"""
Takes all the tokens in pump fun signals and stores them in pumpfun tables and
in case of duplicate tokens, it updates the record and records the history
in the history table
"""

from typing import Optional, Dict, Any, List
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.operations.schema import PumpFunToken
import parsers.PumpfunParser as pumpfunParsers
import requests
from datetime import datetime
from logs.logger import get_logger
from database.pumpfun.PumpfunHandler import PumpFunHandler
from services.AuthService import AuthService
from database.auth.ServiceCredentialsEnum import ServiceCredentials

logger = get_logger(__name__)

class PumpFunAction:
    """Handles complete pump fun signals request workflow"""
    
    def __init__(self, db: SQLitePortfolioDB):
        """
        Initialize action with required parameters
        Args:
            db: Database handler for persistence
        """
        self.db = db
        self.service = ServiceCredentials.CHAINEDGE
        self.baseUrl = self.service.metadata['base_url']

    def processPumpFunTokens(self, cookie: str) -> bool:
        """
        Fetch and persist pump fun tokens
        Args:
            cookie: Validated cookie for API request
        Returns:
            bool: Success status
        """
        try:
            # Make API request with provided cookie
            response = self.hitAPI(cookie)
            if not response:
                logger.error("API request failed")
                return False

            # Parse response into PumpFunToken objects
            pumpFunTokens = pumpfunParsers.parsePumpFunResponse(response)
            if not pumpFunTokens:
                logger.error("No valid items found in response")
                return False

            # Persist to database and get successfully persisted tokens
            persistedTokens = self.persistTokens(pumpFunTokens)
            
            # Push persisted tokens to strategy framework
            if persistedTokens:
                self.pushPumpFunTokensToStrategyFramework(persistedTokens)
                
            return len(persistedTokens) > 0

        except Exception as e:
            logger.error(f"Pump fun signals action failed: {str(e)}")
            return False

    def hitAPI(self, cookie: str) -> Optional[Dict]:
        """Make pump fun signals API request"""
        try:
            # Get fresh access token using service credentials
            authService = AuthService(
                self.db.tokenHandler, 
                self.db,
                self.service
            )
            accessToken = authService.getValidAccessToken()
            
            if not accessToken:
                logger.error("Failed to get valid access token")
                return None
            
            headers = {
                'accept': 'application/json, text/plain, */*',
                'accept-language': 'en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7',
                'authorization': f'Bearer {accessToken}',
                'cookie': cookie,
                'origin': self.service.metadata['web_url'],
                'referer': f"{self.service.metadata['web_url']}/",
                'priority': 'u=1, i',
                'sec-ch-ua': '"Not A(Brand";v="8", "Chromium";v="132", "Microsoft Edge";v="132"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 Edg/132.0.0.0'
            }

            params = {
                'filter_name': 'pumb_fun',
                'refresh': '0'
            }

            # Fix the URL by appending the correct endpoint path
            url = f"{self.baseUrl}/tokensToWatch/"
            
            # Log the request URL for debugging
            logger.info(f"Making request to: {url} with params: {params}")
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            return None

    def persistTokens(self, pumpFunTokens: List[PumpFunToken]) -> List[PumpFunToken]:
        """
        Persist PumpFunToken objects to database
        
        Args:
            pumpFunTokens: List of PumpFunToken objects to persist
            
        Returns:
            List[PumpFunToken]: List of tokens that were successfully persisted
        """
        successfulTokens = []
        try:
            for token in pumpFunTokens:
                try:
                    self.db.pumpfun.insertTokenData(token)
                    successfulTokens.append(token)
                except Exception as token_error:
                    logger.error(f"Failed to persist token {token.tokenid}: {str(token_error)}")
                    continue
                    
            logger.info(f"Successfully persisted {len(successfulTokens)} pump fun tokens")
            return successfulTokens
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise

    def pushPumpFunTokensToStrategyFramework(self, pumpFunTokens: List[PumpFunToken]) -> bool:
        """
        Maps pump fun tokens to PumpFunTokenData objects and pushes them to the strategy framework
        
        Args:
            pumpFunTokens: List of PumpFunToken objects to push to the strategy framework
            
        Returns:
            bool: True if at least one token was successfully pushed, False otherwise
        """
        try:
            if not pumpFunTokens:
                logger.info("No pump fun tokens to push to strategy framework")
                return False
                
            logger.info(f"Pushing {len(pumpFunTokens)} pump fun tokens to strategy framework")
            
            # Import required modules
            from framework.analyticsframework.api.PushTokenFrameworkAPI import PushTokenAPI
            from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
            from framework.analyticsframework.enums.SourceTypeEnum import SourceType
            
            # Initialize analytics handler and push token API
            analyticsHandler = AnalyticsHandler()
            pushTokenAPI = PushTokenAPI(analyticsHandler)
            
            # Process each token
            success_count = 0
            for token in pumpFunTokens:
                try:
                    # Get the current state of the token from the database
                    tokenState = self.db.pumpfun.getTokenState(token.tokenid)
                    if not tokenState:
                        logger.warning(f"Token state not found for {token.tokenid}, skipping")
                        continue
                        
                    # Get token info
                    tokenInfo = self.db.pumpfun.getTokenInfo(token.tokenid)
                    if not tokenInfo:
                        logger.warning(f"Token info not found for {token.tokenid}, skipping")
                        continue
                    
                    # Combine token state and info into a single dictionary
                    combinedTokenData = {**tokenState, **tokenInfo}
                    
                    # Add rug count if available
                    if hasattr(token, 'rugcount'):
                        combinedTokenData['rugcount'] = token.rugcount
                    
                    # Convert to PumpFunTokenData
                    tokenData = PushTokenAPI.mapPumpFunTokenData(combinedTokenData)
                    
                    # Push to strategy framework
                    success = pushTokenAPI.pushToken(
                        tokenData=tokenData,
                        sourceType=SourceType.PUMPFUN.value
                    )
                    
                    if success:
                        success_count += 1
                        logger.info(f"Successfully pushed token {tokenData.tokenid} ({tokenData.tokenname}) to strategy framework")
                    else:
                        logger.warning(f"Failed to push token {tokenData.tokenid} ({tokenData.tokenname}) to strategy framework")
                
                except Exception as token_error:
                    logger.error(f"Error processing token {token.tokenid}: {str(token_error)}")
                    continue
            
            logger.info(f"Successfully pushed {success_count}/{len(pumpFunTokens)} tokens to strategy framework")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to push pump fun tokens to strategy framework: {str(e)}", exc_info=True)
            return False 