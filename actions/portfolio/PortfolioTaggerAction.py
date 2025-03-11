"""
Action to tag portfolio tokens based on defined conditions
"""

from typing import List, Set, Dict
from datetime import datetime, timedelta
import pytz
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.operations.schema import PortfolioSummary
from actions.portfolio.PortfolioTagEnum import PortfolioTokenTag
from logs.logger import get_logger

logger = get_logger(__name__)
IST = pytz.timezone('Asia/Kolkata')

class PortfolioTaggerAction:
    """Handles tagging of portfolio tokens"""
    
    def __init__(self, db: SQLitePortfolioDB):
        """Initialize with database connection"""
        self.db = db
        self.tagMap = PortfolioTokenTag.getTagMap()
        
    def getCurrentTags(self, token: PortfolioSummary) -> Set[str]:
        """Get current tags for a token from database"""
        try:
            if not token.tags:
                return set()
            return set(token.tags.split(','))
        except Exception as e:
            logger.error(f"Error parsing existing tags for token {token.tokenid}: {str(e)}")
            return set()

    def getWalletData(self, tokenId: str) -> List[Dict]:
        """Get wallet data with PNL for a token"""
        try:
            with self.db.conn_manager.transaction() as cursor:
                query = '''
                    SELECT 
                        wi.walletaddress,
                        wi.totalinvestedamount,
                        wi.amounttakenout,
                        sm.profitandloss as chainedgepnl
                    FROM walletsinvested wi
                    LEFT JOIN smartmoneywallets sm ON wi.walletaddress = sm.walletaddress
                    WHERE wi.tokenid = ?
                '''
                cursor.execute(query, (tokenId,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error fetching wallet data for {tokenId}: {str(e)}")
            return []
            
    def evaluateNewTags(self, token: PortfolioSummary) -> Set[str]:
        """Evaluate and get new tags for a token"""
        try:
            # Get wallet data once
            walletData = self.getWalletData(token.tokenid)
            
            # Evaluate all tags with the wallet data
            newTags = set()
            for tagName, checkFunc in self.tagMap.items():
                try:
                    result = checkFunc(token, self.db, walletData)
                    if isinstance(result, set):
                        newTags.update(result)
                    elif result:  # Boolean result
                        newTags.add(tagName)
                except Exception as e:
                    logger.error(f"Error evaluating tag {tagName} for token {token.tokenid}: {str(e)}")
                    continue
            return newTags
        except Exception as e:
            logger.error(f"Error evaluating tags for token {token.tokenid}: {str(e)}")
            return set()

    def addTagsToActivePortSummaryTokens(self) -> bool:
        """
        Tag all active portfolio tokens from the last 24 hours
        
        Returns:
            bool: Success status
        """
        try:
            # Get active tokens from last 24 hours using IST
            oneDayAgo = datetime.now(IST) - timedelta(days=1)
            activeTokens = self.db.portfolio.getActiveTokensSince(oneDayAgo)
            
            if not activeTokens:
                logger.info("No active tokens found for tagging")
                return True
                
            logger.info(f"Found {len(activeTokens)} active tokens to process")
            
            with self.db.transaction() as cursor:
                for token in activeTokens:
                    try:
                        result = self.evaluateAndUpdateTokenTags(token, cursor)
                        if result['tags_changed']:
                            logger.info(f"Updated tags for token {token.tokenid}")
                        else:
                            logger.debug(f"No tag changes for token {token.tokenid}")
                    except Exception as e:
                        logger.error(f"Failed to process token {token.tokenid}: {str(e)}")
                        continue
                        
            return True
            
        except Exception as e:
            logger.error(f"Token tagging failed: {str(e)}")
            return False

    def evaluateAndUpdateTokenTags(self, token, cursor=None) -> dict:
        """
        Evaluate and update tags for a specific token
        
        Args:
            token: Token to evaluate and update tags for
            cursor: Optional database cursor for transaction
            
        Returns:
            dict: Result of tag evaluation and update
        """
        try:
            # Get current tags
            current_tags = self.getCurrentTags(token)
            
            # Evaluate new tags
            new_tags = self.evaluateNewTags(token)
            
            result = {
                'token_id': token.tokenid,
                'current_tags': list(current_tags),
                'new_tags': list(new_tags),
                'tags_changed': new_tags != current_tags,
                'updated': False
            }
            
            # Compare tags
            if new_tags != current_tags:
                logger.info(f"Tags changed for token {token.tokenid}")
                logger.info(f"Old tags: {current_tags}")
                logger.info(f"New tags: {new_tags}")
                
                # Use transaction if cursor provided, otherwise create new one
                with self.db.transaction() as cur:
                    cursor = cursor or cur
                    
                    # First, persist current state to history
                    self.db.portfolio.insertHistory(token, cursor)
                    
                    # Update tags in main table wisth IST timestamp
                    tags = ','.join(sorted(new_tags)) if new_tags else ''
                    currentTime = datetime.now(IST)
                    self.db.portfolio.updateTokenTags(cursor, token.tokenid, tags, currentTime)
                    
                    result['updated'] = True
                    logger.info(f"Updated token {token.tokenid} with new tags at {currentTime.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                logger.debug(f"No tag changes for token {token.tokenid}")
                
            return result
            
        except Exception as e:
            logger.error(f"Failed to process token {token.tokenid}: {str(e)}")
            raise