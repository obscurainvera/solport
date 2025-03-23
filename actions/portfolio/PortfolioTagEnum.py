from enum import Enum
from decimal import Decimal
from typing import Optional, Set, Callable, Dict, List, Tuple
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.operations.schema import PortfolioSummary, WalletsInvested, SmartMoneyWallet
from logs.logger import get_logger
from dataclasses import dataclass

logger = get_logger(__name__)

# Type hint for condition functions
TagCondition = Callable[[PortfolioSummary, SQLitePortfolioDB, Optional[List[Dict]]], Set[str]]

@dataclass
class WalletMetrics:
    """Helper class to store wallet metrics"""
    chainedgePnl: Decimal
    totalInvested: Decimal
    totalTakenOut: Decimal
    walletAddress: str

class PortfolioTokenTag(Enum):
    """Enum to add necessary tags to portfolio tokens"""

    def _checkBalance100k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if smart balance is greater than 100K"""
        try:
            return (token.smartbalance is not None and
                    Decimal(token.smartbalance) > Decimal('100000'))
        except Exception as e:
            logger.error(f"Error checking balance 100k for {token.tokenid}: {str(e)}")
            return False

    def _checkBalance500k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if smart balance is greater than 500K"""
        try:
            return (token.smartbalance is not None and
                    Decimal(token.smartbalance) > Decimal('500000'))
        except Exception as e:
            logger.error(f"Error checking balance 500k for {token.tokenid}: {str(e)}")
            return False

    def _checkBalance1m(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if smart balance is greater than 1M"""
        try:
            return (token.smartbalance is not None and
                    Decimal(token.smartbalance) > Decimal('1000000'))
        except Exception as e:
            logger.error(f"Error checking balance 1M for {token.tokenid}: {str(e)}")
            return False
    
    def _checkHuge1dChange(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if 1d change is beyond ±20%"""
        try:
            return (token.qtychange1d is not None and
                    abs(Decimal(token.qtychange1d)) > Decimal('20'))
        except Exception as e:
            logger.error(f"Error checking 1d change for {token.tokenid}: {str(e)}")
            return False

    def _checkHuge7dChange(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if 7d change is beyond ±20%"""
        try:
            return (token.qtychange7d is not None and
                    abs(Decimal(token.qtychange7d)) > Decimal('20'))
        except Exception as e:
            logger.error(f"Error checking 7d change for {token.tokenid}: {str(e)}")
            return False

    def _checkHuge30dChange(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if 30d change is beyond ±20%"""
        try:
            return (token.qtychange30d is not None and
                    abs(Decimal(token.qtychange30d)) > Decimal('20'))
        except Exception as e:
            logger.error(f"Error checking 30d change for {token.tokenid}: {str(e)}")
            return False

    def _checkPriceWithinRange(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if current price is within 20% increase or decrease of avg price"""
        try:
            return (token.currentprice is not None and
                    token.avgprice is not None and
                    Decimal(token.currentprice) <= Decimal(token.avgprice) * Decimal('1.20') and
                    Decimal(token.currentprice) >= Decimal(token.avgprice) * Decimal('0.80'))
        except Exception as e:
            logger.error(f"Error checking price range for {token.tokenid}: {str(e)}")
            return False

    def _checkMcap0To1m(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is between 0-1M"""
        try:
            return (token.mcap is not None and
                    Decimal('0') <= Decimal(token.mcap) < Decimal('1000000'))
        except Exception as e:
            logger.error(f"Error checking mcap 0-1M for {token.tokenid}: {str(e)}")
            return False

    def _checkMcap1mTo10m(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is between 1M-10M"""
        try:
            return (token.mcap is not None and
                    Decimal('1000000') <= Decimal(token.mcap) < Decimal('10000000'))
        except Exception as e:
            logger.error(f"Error checking mcap 1M-10M for {token.tokenid}: {str(e)}")
            return False

    def _checkMcap10mTo50m(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is between 10M-50M"""
        try:
            return (token.mcap is not None and
                    Decimal('10000000') <= Decimal(token.mcap) < Decimal('50000000'))
        except Exception as e:
            logger.error(f"Error checking mcap 10M-50M for {token.tokenid}: {str(e)}")
            return False

    def _checkMcap50mTo100m(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is between 50M-100M"""
        try:
            return (token.mcap is not None and
                    Decimal('50000000') <= Decimal(token.mcap) < Decimal('100000000'))
        except Exception as e:
            logger.error(f"Error checking mcap 50M-100M for {token.tokenid}: {str(e)}")
            return False

    def _checkMcapAbove100m(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> bool:
        """Check if market cap is above 100M"""
        try:
            return (token.mcap is not None and
                    Decimal(token.mcap) >= Decimal('100000000'))
        except Exception as e:
            logger.error(f"Error checking mcap above 100M for {token.tokenid}: {str(e)}")
            return False

    
    def _getSmartWalletsCount(token: PortfolioSummary, db: SQLitePortfolioDB,
                             minPnl: Decimal, minInvestment: Decimal,
                             walletData: List[Dict]) -> int:
        """Helper function to count smart wallets meeting criteria"""
        try:
            if not walletData:
                return 0
                
            smartWallets = 0
            for wallet in walletData:
                try:
                    # Check PNL from smartmoneywallets table
                    if wallet['chainedgepnl'] is None or Decimal(str(wallet['chainedgepnl'])) < minPnl:
                        continue
                        
                    # Calculate net investment from walletsinvested table
                    # Handle cases where values might be None, null, or 0
                    invested = Decimal('0')
                    if wallet.get('totalinvestedamount') is not None and wallet['totalinvestedamount'] != '':
                        invested = Decimal(str(wallet['totalinvestedamount']))
                    
                    takenOut = Decimal('0')
                    if wallet.get('amounttakenout') is not None and wallet['amounttakenout'] != '':
                        takenOut = Decimal(str(wallet['amounttakenout']))
                    
                    netInvestment = invested - takenOut
                    
                    if netInvestment >= minInvestment:
                        smartWallets += 1
                        
                except Exception as e:
                    # Catch all exceptions to ensure processing continues
                    logger.error(f"Error processing wallet {wallet.get('walletaddress', 'unknown')}: {str(e)}")
                    continue
                    
            return smartWallets
            
        except Exception as e:
            logger.error(f"Error getting smart wallets for {token.tokenid}: {str(e)}")
            return 0

    def _getWalletsInPnlRange(token: PortfolioSummary, db: SQLitePortfolioDB,
                             minPnl: Decimal, maxPnl: Optional[Decimal],
                             walletData: List[Dict]) -> int:
        """Helper function to count wallets in specific PNL range"""
        try:
            if not walletData:
                return 0
                
            walletsCount = 0
            for wallet in walletData:
                try:
                    # Skip if no PNL data
                    if wallet.get('chainedgepnl') is None:
                        continue
                        
                    pnl = Decimal(str(wallet['chainedgepnl']))
                    
                    # Check if PNL is in range
                    if pnl < minPnl:
                        continue
                        
                    # If maxPnl is specified, check upper bound too
                    if maxPnl is not None and pnl >= maxPnl:
                        continue
                        
                    walletsCount += 1
                        
                except Exception as e:
                    logger.error(f"Error processing wallet PNL for {wallet.get('walletaddress', 'unknown')}: {str(e)}")
                    continue
                    
            return walletsCount
            
        except Exception as e:
            logger.error(f"Error counting wallets in PNL range for {token.tokenid}: {str(e)}")
            return 0

    def _getWalletsInInvestmentRange(token: PortfolioSummary, db: SQLitePortfolioDB,
                                    minInvestment: Decimal, maxInvestment: Optional[Decimal],
                                    walletData: List[Dict]) -> int:
        """Helper function to count wallets with investment in specific range"""
        try:
            if not walletData:
                return 0
                
            walletsCount = 0
            for wallet in walletData:
                try:
                    # Calculate net investment from walletsinvested table
                    invested = Decimal('0')
                    if wallet.get('totalinvestedamount') is not None and wallet['totalinvestedamount'] != '':
                        invested = Decimal(str(wallet['totalinvestedamount']))
                    
                    takenOut = Decimal('0')
                    if wallet.get('amounttakenout') is not None and wallet['amounttakenout'] != '':
                        takenOut = Decimal(str(wallet['amounttakenout']))
                    
                    netInvestment = invested - takenOut
                    
                    # Check if investment is in range
                    if netInvestment < minInvestment:
                        continue
                        
                    # If maxInvestment is specified, check upper bound too
                    if maxInvestment is not None and netInvestment >= maxInvestment:
                        continue
                        
                    walletsCount += 1
                        
                except Exception as e:
                    logger.error(f"Error processing wallet investment for {wallet.get('walletaddress', 'unknown')}: {str(e)}")
                    continue
                    
            return walletsCount
            
        except Exception as e:
            logger.error(f"Error counting wallets in investment range for {token.tokenid}: {str(e)}")
            return 0

    def _check300kTo10k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Check smart wallets with >300K PNL and >10K investment"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getSmartWalletsCount(
                token, db,
                minPnl=Decimal('300000'),
                minInvestment=Decimal('10000'),
                walletData=walletData
            )
            
            if walletCount >= 3:
                return {"SMART_300K_10K_3"}
            elif walletCount >= 2:
                return {"SMART_300K_10K_2"}
            elif walletCount >= 1:
                return {"SMART_300K_10K_1"}
            return set()
        except Exception as e:
            logger.error(f"Error checking 300K/10K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _check500kTo30k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Check smart wallets with >500K PNL and >30K investment"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getSmartWalletsCount(
                token, db,
                minPnl=Decimal('500000'),
                minInvestment=Decimal('30000'),
                walletData=walletData
            )
            
            if walletCount >= 3:
                return {"SMART_500K_30K_3"}
            elif walletCount >= 2:
                return {"SMART_500K_30K_2"}
            elif walletCount >= 1:
                return {"SMART_500K_30K_1"}
            return set()
        except Exception as e:
            logger.error(f"Error checking 500K/30K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _check1mTo100k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Check smart wallets with >1M PNL and >100K investment"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getSmartWalletsCount(
                token, db,
                minPnl=Decimal('1000000'),
                minInvestment=Decimal('100000'),
                walletData=walletData
            )
            
            if walletCount >= 3:
                return {"SMART_1M_100K_3"}
            elif walletCount >= 2:
                return {"SMART_1M_100K_2"}
            elif walletCount >= 1:
                return {"SMART_1M_100K_1"}
            return set()
        except Exception as e:
            logger.error(f"Error checking 1M/100K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _checkPnl0To400k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Count wallets with PNL between 0-400K"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getWalletsInPnlRange(
                token, db,
                minPnl=Decimal('0'),
                maxPnl=Decimal('400000'),
                walletData=walletData
            )
            
            if walletCount > 0:
                return {f"PNL_0-400K_{walletCount}"}
            return set()
        except Exception as e:
            logger.error(f"Error checking PNL 0-400K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _checkPnl400kTo1m(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Count wallets with PNL between 400K-1M"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getWalletsInPnlRange(
                token, db,
                minPnl=Decimal('400000'),
                maxPnl=Decimal('1000000'),
                walletData=walletData
            )
            
            if walletCount > 0:
                return {f"PNL_400K-1M_{walletCount}"}
            return set()
        except Exception as e:
            logger.error(f"Error checking PNL 400K-1M wallets for {token.tokenid}: {str(e)}")
            return set()

    def _checkPnlAbove1m(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Count wallets with PNL above 1M"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getWalletsInPnlRange(
                token, db,
                minPnl=Decimal('1000000'),
                maxPnl=None,
                walletData=walletData
            )
            
            if walletCount > 0:
                return {f"PNL_>1M_{walletCount}"}
            return set()
        except Exception as e:
            logger.error(f"Error checking PNL >1M wallets for {token.tokenid}: {str(e)}")
            return set()

    def _checkAi1kTo10k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Count wallets with investment between 1K-10K"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getWalletsInInvestmentRange(
                token, db,
                minInvestment=Decimal('1000'),
                maxInvestment=Decimal('10000'),
                walletData=walletData
            )
            
            if walletCount > 0:
                return {f"AI_1K-10K_{walletCount}"}
            return set()
        except Exception as e:
            logger.error(f"Error checking AI 1K-10K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _checkAi10kTo50k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Count wallets with investment between 10K-50K"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getWalletsInInvestmentRange(
                token, db,
                minInvestment=Decimal('10000'),
                maxInvestment=Decimal('50000'),
                walletData=walletData
            )
            
            if walletCount > 0:
                return {f"AI_10K-50K_{walletCount}"}
            return set()
        except Exception as e:
            logger.error(f"Error checking AI 10K-50K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _checkAi50kTo100k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Count wallets with investment between 50K-100K"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getWalletsInInvestmentRange(
                token, db,
                minInvestment=Decimal('50000'),
                maxInvestment=Decimal('100000'),
                walletData=walletData
            )
            
            if walletCount > 0:
                return {f"AI_50K-100K_{walletCount}"}
            return set()
        except Exception as e:
            logger.error(f"Error checking AI 50K-100K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _checkAi100kTo500k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Count wallets with investment between 100K-500K"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getWalletsInInvestmentRange(
                token, db,
                minInvestment=Decimal('100000'),
                maxInvestment=Decimal('500000'),
                walletData=walletData
            )
            
            if walletCount > 0:
                return {f"AI_100K-500K_{walletCount}"}
            return set()
        except Exception as e:
            logger.error(f"Error checking AI 100K-500K wallets for {token.tokenid}: {str(e)}")
            return set()

    def _checkAiAbove500k(token: PortfolioSummary, db: SQLitePortfolioDB, walletData: Optional[List[Dict]] = None) -> Set[str]:
        """Count wallets with investment above 500K"""
        try:
            if not walletData:
                return set()
                
            walletCount = PortfolioTokenTag._getWalletsInInvestmentRange(
                token, db,
                minInvestment=Decimal('500000'),
                maxInvestment=None,
                walletData=walletData
            )
            
            if walletCount > 0:
                return {f"AI_>500K_{walletCount}"}
            return set()
        except Exception as e:
            logger.error(f"Error checking AI >500K wallets for {token.tokenid}: {str(e)}")
            return set()
    
    # Balance tags
    BALANCE_100K = ("BALANCE_100K", _checkBalance100k)
    BALANCE_500K = ("BALANCE_500K", _checkBalance500k)
    BALANCE_1M = ("BALANCE_1M", _checkBalance1m)
    
    # Price change tags
    HUGE_1D_CHANGE = ("HUGE_1D_CHANGE", _checkHuge1dChange)
    HUGE_7D_CHANGE = ("HUGE_7D_CHANGE", _checkHuge7dChange)
    HUGE_30D_CHANGE = ("HUGE_30D_CHANGE", _checkHuge30dChange)
    PRICE_WITHIN_RANGE = ("PRICE_WITHIN_RANGE", _checkPriceWithinRange)
    
    # Market cap range tags
    MCAP_0_1M = ("MCAP_0_1M", _checkMcap0To1m)
    MCAP_1M_10M = ("MCAP_1M_10M", _checkMcap1mTo10m)
    MCAP_10M_50M = ("MCAP_10M_50M", _checkMcap10mTo50m)
    MCAP_50M_100M = ("MCAP_50M_100M", _checkMcap50mTo100m)
    MCAP_ABOVE_100M = ("MCAP_ABOVE_100M", _checkMcapAbove100m)

    # Smart wallet investment tags
    SMART_300K_10K = ("SMART_300K_10K", _check300kTo10k)
    SMART_500K_30K = ("SMART_500K_30K", _check500kTo30k)
    SMART_1M_100K = ("SMART_1M_100K", _check1mTo100k)
    
    # PNL range tags - count wallets in each PNL range
    PNL_0_400K = ("PNL_0_400K", _checkPnl0To400k)
    PNL_400K_1M = ("PNL_400K_1M", _checkPnl400kTo1m)
    PNL_ABOVE_1M = ("PNL_ABOVE_1M", _checkPnlAbove1m)
    
    # Amount Invested (AI) range tags - count wallets in each investment range
    AI_1K_10K = ("AI_1K_10K", _checkAi1kTo10k)
    AI_10K_50K = ("AI_10K_50K", _checkAi10kTo50k)
    AI_50K_100K = ("AI_50K_100K", _checkAi50kTo100k)
    AI_100K_500K = ("AI_100K_500K", _checkAi100kTo500k)
    AI_ABOVE_500K = ("AI_ABOVE_500K", _checkAiAbove500k)

    def __init__(self, tagName: str, conditionFunc: TagCondition):
        self.tagName = tagName
        self.conditionFunc = conditionFunc

    @classmethod
    def getTagMap(cls) -> Dict[str, TagCondition]:
        """Get mapping of all tags to their condition functions"""
        return {tag.tagName: tag.conditionFunc for tag in cls}

    def __str__(self) -> str:
        return self.tagName
        
    @classmethod
    def getAllTags(cls) -> List[str]:
        """Get list of all tag values"""
        return [tag.tagName for tag in cls]