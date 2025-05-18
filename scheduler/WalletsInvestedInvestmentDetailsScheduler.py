from typing import List, Dict
from database.operations.sqlite_handler import SQLitePortfolioDB
from config.Security import COOKIE_MAP, isValidCookie
from logs.logger import get_logger
from actions.WalletsInvestedInvestmentDetailsAction import WalletsInvestedInvestmentDetailsAction
import time
import random
from decimal import Decimal

logger = get_logger(__name__)

class WalletsInvestedInvestmentDetailsScheduler:
    """Manages transaction analysis for token wallets"""
    
    def __init__(self, db_path: str = 'portfolio.db'):
        """
        Initialize scheduler with database instance
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db = SQLitePortfolioDB(db_path)
        self.action = WalletsInvestedInvestmentDetailsAction(self.db)
        logger.info(f"Transaction Analysis scheduler initialized with database: {db_path}")

    def analyzeSMWalletInvestment(self, minSmartHolding: Decimal = None):
        """
        Process all active token wallets for transaction analysis
        
        Args:
            min_smart_holding: Minimum smart holding threshold (optional)
        """
        validCookies = [
            cookie for cookie in COOKIE_MAP.get('solscan', {})
            if isValidCookie(cookie, 'solscan')
        ]

        if not validCookies:
            logger.warning("No valid cookies available for solscan API")
            return

        # Use provided threshold or default from action
        threshold = minSmartHolding or self.action.MIN_SMART_HOLDING
        
        for cookie in validCookies:
            try:
                logger.info(f"Using cookie: {cookie[:15]}...")
                
                # Get all active token wallets with minimum smart holding for a specific token
                walletsWithHighSMTokenHoldings = self.db.walletsInvested.getWalletsWithHighSMTokenHoldings(
                    minBalance=threshold, 
                    tokenId=None
                )
                
                logger.info(f"Found {len(walletsWithHighSMTokenHoldings)} active wallets for investement analysis with min holding {threshold}")
                
                for wallet in walletsWithHighSMTokenHoldings:
                    try:
                        logger.info(f"Processing transactions for wallet {wallet['walletaddress']} token {wallet['tokenname']} ({wallet['tokenid']})")
                        success = self.action.updateInvestmentData(
                            cookie=cookie,
                            walletAddress=wallet['walletaddress'],
                            tokenId=wallet['tokenid'],
                            walletInvestedId=wallet['walletinvestedid']
                        )
                        
                        if success:
                            logger.info(f"Successfully analyzed wallet {wallet['walletaddress']} for {wallet['tokenname']}")
                        else:
                            logger.warning(f"Failed to analyze wallet {wallet['walletaddress']} for {wallet['tokenname']}")
                        
                        
                    except Exception as e:
                        logger.error(f"Failed to process wallet {wallet['walletaddress']}: {str(e)}")
                        continue
                    
            except Exception as e:
                logger.error(f"Failed to execute transaction analysis: {str(e)}")
                
    def handleInvestmentDetailsOfAllWalletsInvestedInAToken(self, tokenId: str, cookie: str = None, minHolding: Decimal = None):
        """
        Process all wallets invested in a specific token for transaction analysis
        
        Args:
            tokenId: The token ID to analyze
            cookie: Solscan cookie for API access (optional)
        """
        if not tokenId:
            logger.error("Token ID is required")
            return False
            
        # Use provided cookie or get a valid one
        if not cookie:
            validCookies = [
                c for c in COOKIE_MAP.get('solscan', {})
                if isValidCookie(c, 'solscan')
            ]
            
            if not validCookies:
                logger.warning("No valid cookies available for solscan API")
                return False
                
            cookie = validCookies[0]
        
        try:
            logger.info(f"Analyzing all wallets invested in token {tokenId}")
            
            # Get all wallets invested in the specific token
            walletsInvestedInToken = self.db.walletsInvested.getWalletsWithHighSMTokenHoldings(minBalance=minHolding, tokenId=tokenId)
            
            if not walletsInvestedInToken:
                logger.warning(f"No wallets found for token {tokenId}")
                return False
                
            logger.info(f"Found {len(walletsInvestedInToken)} wallets invested in token {tokenId}")
            
            for wallet in walletsInvestedInToken:
                try:
                    walletAddress = wallet['walletaddress']
                    walletInvestedId = wallet['walletinvestedid']
                    
                    logger.info(f"Processing transactions for wallet {walletAddress} token {tokenId}")
                    
                    success = self.action.updateInvestmentData(
                        cookie=cookie,
                        walletAddress=walletAddress,
                        tokenId=tokenId,
                        walletInvestedId=walletInvestedId
                    )
                    
                    if success:
                        logger.info(f"Successfully analyzed wallet {walletAddress}")
                    else:
                        logger.warning(f"Failed to analyze wallet {walletAddress}")

                    
                except Exception as e:
                    logger.error(f"Failed to process wallet {walletAddress}: {str(e)}")
                    continue
                
            return True
                
        except Exception as e:
            logger.error(f"Failed to execute transaction analysis for token {tokenId}: {str(e)}")
            return False