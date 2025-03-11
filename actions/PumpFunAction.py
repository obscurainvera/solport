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

            # Persist to database
            self.persistTokens(pumpFunTokens)
            return True

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

    def persistTokens(self, pumpFunTokens: List[PumpFunToken]) -> None:
        """
        Persist PumpFunToken objects to database
        
        Args:
            pumpFunTokens: List of PumpFunToken objects to persist
        """
        try:
            for token in pumpFunTokens:
                self.db.pumpfun.insertTokenData(token)
            logger.info(f"Successfully persisted {len(pumpFunTokens)} pump fun tokens")
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise 