"""
Action for fetching and storing top traders data from Chainedge API
"""
from typing import Dict, List, Any, Optional
import requests
from datetime import datetime
import pytz
from logs.logger import get_logger
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.toptraders.TopTradersHandler import TopTradersHandler
from parsers.TopTradersParser import TopTradersParser
from database.auth.TokenHandler import TokenHandler
from database.auth.ServiceCredentialsEnum import ServiceCredentials
from config.Security import isValidCookie
from config.Security import COOKIE_MAP

logger = get_logger(__name__)

class TopTradersAction:
    """Handles the complete top traders data fetching and storage workflow"""
    
    def __init__(self, db: SQLitePortfolioDB):
        """
        Initialize the action with required parameters
        
        Args:
            db: Database handler for persistence
        """
        self.db = db
        self.parser = TopTradersParser()
        self.handler = TopTradersHandler(self.db.conn_manager)
    
    def getAuthCookie(self, cookie: str) -> Optional[str]:
        """
        Get the authentication cookie for the API
        
        Returns:
            Optional[str]: The cookie string if valid, None otherwise
        """
        try:    
            # Validate the cookie
            if not isValidCookie(cookie, 'toptraders'):
                logger.error("Invalid or expired cookie")
                return None
                
            return cookie
            
        except Exception as e:
            logger.error(f"Error getting auth cookie: {e}")
            return None
    
    def fetchTopTraders(self, cookie: str) -> Optional[Dict]:
        """
        Fetch top traders data from the API
        
        Args:
            cookie: Valid authentication cookie
            
        Returns:
            Optional[Dict]: API response data or None if failed
        """
        try:
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.9',
                'referer': 'https://app.chainedge.io/insights/',
                'sec-ch-ua': '"Chromium";v="136", "Not.A/Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                'x-requested-with': 'XMLHttpRequest',
                'cookie': cookie
            }
            
            # Build the API URL with parameters
            url = "https://app.chainedge.io/pnl_ens_name_solana/"
            params = {
                'draw': '2',
                'columns[0][data]': 'wallet_ens_name',
                'columns[0][name]': '',
                'columns[0][searchable]': 'true',
                'columns[0][orderable]': 'false',
                'columns[0][search][value]': '',
                'columns[0][search][regex]': 'false',
                'columns[1][data]': 'tokenname',
                'columns[1][name]': '',
                'columns[1][searchable]': 'true',
                'columns[1][orderable]': 'false',
                'columns[1][search][value]': '',
                'columns[1][search][regex]': 'false',
                'columns[2][data]': 'chain',
                'columns[2][name]': '',
                'columns[2][searchable]': 'true',
                'columns[2][orderable]': 'false',
                'columns[2][search][value]': '',
                'columns[2][search][regex]': 'false',
                'columns[3][data]': 'pnl',
                'columns[3][name]': '',
                'columns[3][searchable]': 'true',
                'columns[3][orderable]': 'true',
                'columns[3][search][value]': '',
                'columns[3][search][regex]': 'false',
                'columns[4][data]': 'avgentry',
                'columns[4][name]': '',
                'columns[4][searchable]': 'true',
                'columns[4][orderable]': 'true',
                'columns[4][search][value]': '',
                'columns[4][search][regex]': 'false',
                'columns[5][data]': 'avgexit',
                'columns[5][name]': '',
                'columns[5][searchable]': 'true',
                'columns[5][orderable]': 'true',
                'columns[5][search][value]': '',
                'columns[5][search][regex]': 'false',
                'columns[6][data]': 'start_period',
                'columns[6][name]': '',
                'columns[6][searchable]': 'true',
                'columns[6][orderable]': 'true',
                'columns[6][search][value]': '',
                'columns[6][search][regex]': 'false',
                'order[0][column]': '0',
                'order[0][dir]': 'asc',
                'start': '0',
                'length': '10000',  # Adjust based on how many records you want to fetch
                'search[value]': '',
                'search[regex]': 'false',
                'cache': '0',
                'D_30': '30D',
                '_': str(int(datetime.now().timestamp() * 1000))
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching top traders data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in fetch_top_traders: {e}")
            return None
    
    def getAllLatestTopTraders(self) -> bool:
        """
        Main method to process top traders data
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            validCookies = [
            cookie for cookie in COOKIE_MAP.get('toptrader', {})
            if isValidCookie(cookie, 'toptrader')
        ]

            if not validCookies:
                logger.warning("No valid cookies available for attention API")
                return False
            
            # Fetch data from API
            logger.info("Fetching top traders data from API")
            latestTopTradersData = self.fetchTopTraders(validCookies[0])
            if not latestTopTradersData:
                logger.error("Failed to fetch top traders data")
                return False
            
            # Parse the response
            logger.info("Parsing API response")
            topTradersData = self.parser.parseResponse(latestTopTradersData)
            if not topTradersData:
                logger.error("No valid trader data found in response")
                return False
            
            # Store in database
            logger.info(f"Storing {len(topTradersData)} trader records in database")
            success = self.handler.batchUpsertTraders(topTradersData)
            
            if success:
                logger.info("Successfully processed top traders data")
            else:
                logger.error("Failed to store top traders data")
                
            return success
            
        except Exception as e:
            logger.error(f"Error in process_top_traders: {e}")
            return False
