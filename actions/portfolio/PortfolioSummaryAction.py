"""
Takes all the tokens in portfolio summary and stores them in portfolio_summary table and
in case of duplicate tokens, it updates the record and records the history
in the history table
"""

from typing import Optional, Dict, Any, List, Union
from actions.portfolio.PortfolioTagEnum import PortfolioTokenTag
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.operations.schema import PortfolioSummary
import logging
import parsers.PortSummaryParser as PortSummaryParser
import requests
from config.Security import COOKIE_MAP, isValidCookie
from decimal import Decimal
import time
from datetime import datetime
from logs.logger import get_logger
from framework.analyticsframework.api.PushTokenFrameworkAPI import PushTokenAPI
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from framework.analyticsframework.enums.SourceTypeEnum import SourceType    

logger = get_logger(__name__)

class PortfolioSummaryAction:
    """Handles complete portfolio summary request workflow"""
    
    def __init__(self, db: SQLitePortfolioDB):
        """
        Initialize action with required security parameters
        Args:
            db: Database handler for authentication
        """
        self.db = db
        self.session = requests.Session()
        self._configure_headers()
        self.timeout = 60
        self.max_retries = 3

    def _configure_headers(self):
        """Set headers from endpoint configuration"""
        self.headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-IN,en-GB;q=0.9,en;q=0.8,en-US;q=0.7',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': "https://app.chainedge.io",
            'Priority ': 'u=1, i',
            'Referer': "https://app.chainedge.io/portfolio_summary/",
            'Sec-Ch-Ua': '"Microsoft Edge";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"macOS"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
            'X-Requested-With': 'XMLHttpRequest'
        }

    def _buildPayload(self, marketAge: list, pnlWallet: int, ownership: int) -> Dict[str, str]:
        """
        Construct payload with dynamic parameters
        
        Args:
            marketAge (List[str]): List of market age ranges
            pnlWallet (Union[int, float, Decimal]): PNL wallet threshold value
            ownership (Union[int, float, Decimal]): Ownership threshold value
        """
        # Base payload structure
        payload = {
            'draw': '4',
            'start': '0',
            'length': '40',
            'search[value]': '',
            'search[regex]': 'false',
            'solana': '1',
            'portfolio_topfilter_id': '1000',
            'order[0][column]': '1',
            'order[0][dir]': 'desc',
            'market_age': str(marketAge),
            'pnl_wallet': str(float(pnlWallet)),
            'ownership': str(float(ownership))
        }

        # Add column configurations
        columns = [
            {'data': 'name', 'orderable': 'false'},
            {'data': 'smart_balance', 'orderable': 'true'},
            {'data': 'd1_chg_pct', 'orderable': 'true'},
            {'data': 'd7_chg_pct', 'orderable': 'true'},
            {'data': 'd30_chg_pct', 'orderable': 'true'},
            {'data': 'avg_buy_price', 'orderable': 'true'},
            {'data': 'price_1h', 'orderable': 'false'},
            {'data': 'fdv_or_mcap', 'orderable': 'false'},
            {'data': 'liquidity', 'orderable': 'false'},
            {'data': 'tokenagetoday', 'orderable': 'true'},
            {'data': 'w_countgrt_1000', 'orderable': 'true'},
            {'data': 'w_countgrt_5000', 'orderable': 'true'},
            {'data': 'w_countgrt_10000', 'orderable': 'true'},
            {'data': 'change_pct_1h', 'orderable': 'false'},
            {'data': 'change_pct_30d', 'orderable': 'false'},
            {'data': 'change_pct_24h', 'orderable': 'false'},
            {'data': 'volume24', 'orderable': 'false'}
        ]

        for i, col in enumerate(columns):
            payload[f'columns[{i}][data]'] = col['data']
            payload[f'columns[{i}][name]'] = ''
            payload[f'columns[{i}][searchable]'] = 'true'
            payload[f'columns[{i}][orderable]'] = col['orderable']
            payload[f'columns[{i}][search][value]'] = ''
            payload[f'columns[{i}][search][regex]'] = 'false'

        return payload

    def getPortfolioSummaryAPIData(self, cookie: str, marketAge: list, pnlWallet: int, ownership: int) -> Optional[Dict[str, Any]]:
        """Execute portfolio request with retry only on failure"""
        startTime = time.time()
        try:
            payload = self._buildPayload(marketAge, pnlWallet, ownership)
            
            response = self.session.post(
                'https://app.chainedge.io/god_portfoliojson/',
                headers={**self.headers, 'Cookie': cookie},
                data=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            if not response.content:
                raise ValueError("Empty response received")

            parsedItems = PortSummaryParser.parsePortSummaryAPIResponse(response.json())
            
            if parsedItems:
                self.persistPortfolioSummaryData(parsedItems, marketAge)
                logger.debug(f"Successfully processed {len(parsedItems)} items")
                executionTime = time.time() - startTime
                logger.debug(f"Action completed in {executionTime:.2f} seconds for market age {marketAge}")
                return parsedItems
            else:
                logger.warning(f"\nNo valid items to persist\nMarket Age: {marketAge}\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                executionTime = time.time() - startTime
                logger.debug(f"Action completed in {executionTime:.2f} seconds for market age {marketAge}")
                return None
                
        except (requests.RequestException, ValueError) as e:
            # Only retry on request/response errors
            for attempt in range(1, self.max_retries):
                logger.error(f"Request failed (attempt {attempt}/{self.max_retries}): {str(e)}")
                time.sleep(2 ** attempt)  # Exponential backoff
                
                try:
                    response = self.session.post(
                        'https://app.chainedge.io/god_portfoliojson/',
                        headers={**self.headers, 'Cookie': cookie},
                        data=payload,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    
                    if not response.content:
                        continue  # Try next attempt if empty response
                        
                    parsedItems = PortSummaryParser.parsePortSummaryAPIResponse(response.json())
                    if parsedItems:
                        self.persistPortfolioSummaryData(parsedItems, marketAge)
                        logger.info(f"Successfully processed {len(parsedItems)} items on retry {attempt}")
                        execution_time = time.time() - startTime
                        logger.info(f"Action completed in {execution_time:.2f} seconds for market age {marketAge}")
                        return parsedItems
                        
                except Exception as retry_error:
                    logger.error(f"Retry failed: {str(retry_error)}")
                    continue
                    
            logger.error("All retry attempts failed")
            execution_time = time.time() - startTime
            logger.error(f"Action failed after {execution_time:.2f} seconds: {str(e)}")
            return None
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            execution_time = time.time() - startTime
            logger.error(f"Action failed after {execution_time:.2f} seconds: {str(e)}")
            return None

    def persistPortfolioSummaryData(self, items: List[PortfolioSummary], market_age: list):
        """
        Persist portfolio items to database with transaction management
        
        Args:
            items: List of PortfolioSummary objects to persist
            
        Note:
            Uses transaction to ensure atomic updates
            Handles both new insertions and updates to existing records
        """
        try:
            tokenIds = [item.tokenid for item in items]
            existingRecords = self.db.getTokenData(tokenIds)
            existingMap = {record.tokenid: record for record in existingRecords}
            current_time = datetime.now()

            with self.db.transaction() as cursor:
                for item in items:
                    try:
                        # Ensure createdat and updatedat are set
                        if not hasattr(item, 'createdat') or item.createdat is None:
                            item.createdat = current_time
                        if not hasattr(item, 'updatedat') or item.updatedat is None:
                            item.updatedat = current_time
                        
                        if item.tokenid in existingMap:
                            # Insert history record first
                            existing_item = existingMap[item.tokenid]
                            # Preserve original createdat from existing record
                            if hasattr(existing_item, 'createdat') and existing_item.createdat is not None:
                                item.createdat = existing_item.createdat
                            self.db.insertHistory(existing_item, cursor)
                            # Then update current record
                            self.db.updateSummary(item, cursor)
                            logger.info(f"Updated existing record for token {item.tokenid} with name {item.name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {market_age}")
                        else:
                            # Insert new record
                            self.db.insertSummary(item, cursor)
                            logger.info(f"Inserted new record for token {item.tokenid} with name {item.name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {market_age}")
                    except Exception as e:
                        logger.error(f"Failed to persist item {item.tokenid} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {market_age}: {str(e)}")
                        raise

            logger.info(f"Successfully persisted {len(items)} items at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} with market age {market_age}")
            
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            raise
        
    def pushPortSummaryTokensToStrategyFramework(self):
        """
        Pushes the portfolio summary tokens to the strategy framework
        """
        try:
            # Get all tokens from portfolio summary
            tokens = self.db.getActivePortfolioTokens()
            
            if not tokens:
                logger.info("No active tokens found in portfolio summary")
                return False
            
            logger.info(f"Found {len(tokens)} active tokens in portfolio summary")

            
            # Initialize analytics handler and push token API
            analyticsHandler = AnalyticsHandler()
            pushTokenAPI = PushTokenAPI(analyticsHandler)
            
            # Process each token
            success_count = 0
            for token in tokens:
                try:
                    # Convert to PortSummaryTokenData
                    tokenData = PushTokenAPI.mapPortfolioTokenData(token)
                    
                    # Push to strategy framework
                    success = pushTokenAPI.pushToken(
                        tokenData=tokenData,
                        sourceType=SourceType.PORTSUMMARY.value
                    )
                    
                    if success:
                        success_count += 1
                        logger.info(f"Successfully pushed token {tokenData.tokenid} ({tokenData.tokenname}) to strategy framework")
                    else:
                        logger.warning(f"Failed to push token {tokenData.tokenid} ({tokenData.tokenname}) to strategy framework")
                
                except Exception as token_error:
                    logger.error(f"Error processing token {token.get('tokenid', 'unknown')}: {str(token_error)}")
                    continue
            
            logger.info(f"Successfully pushed {success_count}/{len(tokens)} tokens to strategy framework")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to push portfolio summary tokens to strategy framework: {str(e)}", exc_info=True)
            return False
