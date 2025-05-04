from database.operations.base_handler import BaseSQLiteHandler
from typing import List, Dict, Optional, Any, Tuple
from decimal import Decimal
import sqlite3
from logs.logger import get_logger
from datetime import datetime
import json
import time

logger = get_logger(__name__)

class SuperPortReportHandler(BaseSQLiteHandler):
    """
    Handler for combined report operations.
    Joins data from portsummary, walletsinvested, attentiontokenregistry, and smartmoneywallets tables
    to provide comprehensive token analysis.
    """
    
    def __init__(self, conn_manager):
        """
        Initialize the handler with a connection manager.
        
        Args:
            conn_manager: Database connection manager instance
        """
        super().__init__(conn_manager)
    
    def getSuperPortReport(self, 
                          tokenId: str = None, 
                          name: str = None, 
                          chainName: str = None,
                          minMarketCap: float = None,
                          maxMarketCap: float = None,
                          minTokenAge: float = None,
                          maxTokenAge: float = None,
                          minAttentionCount: int = None,
                          sortBy: str = "smartbalance",
                          sortOrder: str = "desc",
                          walletCategory: str = None,
                          walletType: str = None,
                          minWalletCount: int = 0,
                          minAmountInvested: float = 0) -> List[Dict[str, Any]]:
        """
        Get combined report data with optional filters.
        
        Args:
            tokenId: Filter by token ID (partial match)
            name: Filter by token name (partial match)
            chainName: Filter by chain name (partial match)
            minMarketCap: Minimum market cap filter
            maxMarketCap: Maximum market cap filter
            minTokenAge: Minimum token age filter
            maxTokenAge: Maximum token age filter
            minAttentionCount: Minimum attention count filter
            sortBy: Field to sort by (default: smartbalance)
            sortOrder: Sort order (asc or desc, default: desc)
            
        Returns:
            List of combined report data dictionaries
        """
        start_time = time.time()
        logger.info(f"Starting SuperPortReport query with filters: tokenId={tokenId}, name={name}, chainName={chainName}")
        
        # Build the base query for token information
        query, params = self._build_base_query(
            tokenId=tokenId,
            name=name,
            chainName=chainName,
            minMarketCap=minMarketCap,
            maxMarketCap=maxMarketCap,
            minTokenAge=minTokenAge,
            maxTokenAge=maxTokenAge,
            minAttentionCount=minAttentionCount,
            sortBy=sortBy,
            sortOrder=sortOrder
        )
        # Execute query to get token data
        with self.transaction() as cursor:
            cursor.execute(query, params)
            tokens = cursor.fetchall()
            
            # Process token data
            superPortReportData = self._process_token_data(cursor, tokens)
            
            # Apply wallet breakdown filters if specified
            if walletCategory or walletType or minWalletCount > 0 or minAmountInvested > 0:
                superPortReportData = self.filterTokensByWalletBreakdown(
                    superPortReportData,
                    category=walletCategory,
                    type_filter=walletType,
                    min_wallets=minWalletCount,
                    min_amount=minAmountInvested
                )
            
            # Log performance metrics
            end_time = time.time()
            execution_time = end_time - start_time
            logger.info(f"SuperPortReport query completed in {execution_time:.2f} seconds, found {len(superPortReportData)} tokens")
            
            return superPortReportData

    def _build_base_query(self, tokenId=None, name=None, chainName=None, minMarketCap=None, 
                        maxMarketCap=None, minTokenAge=None, maxTokenAge=None, 
                        minAttentionCount=None, sortBy="smartbalance", sortOrder="desc") -> Tuple[str, List]:
        """
        Build the base SQL query and parameters for token filtering.
        
        Args:
            tokenId: Filter by token ID (partial match)
            name: Filter by token name (partial match)
            chainName: Filter by chain name (partial match)
            minMarketCap: Minimum market cap filter
            maxMarketCap: Maximum market cap filter
            minTokenAge: Minimum token age filter
            maxTokenAge: Maximum token age filter
            minAttentionCount: Minimum attention count filter
            sortBy: Field to sort by (default: smartbalance)
            sortOrder: Sort order (asc or desc, default: desc)
            
        Returns:
            Tuple of (query_string, params_list)
        """
        # Base query for token information
        query = """
            SELECT 
                p.portsummaryid,
                p.chainname,
                p.tokenid,
                p.name,
                p.tokenage,
                p.mcap,
                p.avgprice,
                p.smartbalance,
                COALESCE(att.currentstatus, 'UNKNOWN') as attention_status,
                COALESCE(att.attentioncount, 0) as attention_count,
                (SELECT COUNT(*) FROM walletsinvested w WHERE w.tokenid = p.tokenid AND w.status = 1) as total_wallets
            FROM portsummary p
            LEFT JOIN attentiontokenregistry att ON p.tokenid = att.tokenid
            WHERE p.status = 1
        """
        params = []

        # Add filters based on parameters
        if tokenId:
            query += " AND p.tokenid LIKE ?"
            params.append(f"%{tokenId}%")
        
        if name:
            query += " AND p.name LIKE ?"
            params.append(f"%{name}%")
        
        if chainName:
            query += " AND p.chainname LIKE ?"
            params.append(f"%{chainName}%")
        
        if minMarketCap is not None:
            query += " AND p.mcap >= ?"
            params.append(minMarketCap)
        
        if maxMarketCap is not None:
            query += " AND p.mcap <= ?"
            params.append(maxMarketCap)
        
        if minTokenAge is not None:
            query += " AND CAST(p.tokenage AS FLOAT) >= ?"
            params.append(minTokenAge)
        
        if maxTokenAge is not None:
            query += " AND CAST(p.tokenage AS FLOAT) <= ?"
            params.append(maxTokenAge)
            
        if minAttentionCount is not None:
            query += " AND att.attentioncount >= ?"
            params.append(minAttentionCount)
            
        # Validate sort parameters
        validSortFields = ["portsummaryid", "chainname", "tokenid", "name", "tokenage", "mcap", 
                            "avgprice", "smartbalance", "attention_count", "total_wallets"]
        validSortOrders = ["asc", "desc"]
        
        if sortBy not in validSortFields:
            sortBy = "smartbalance"
        
        if sortOrder.lower() not in validSortOrders:
            sortOrder = "desc"
            
        # Add sorting
        sort_field = sortBy
        if sortBy == "attention_count":
            sort_field = "att.attentioncount"
        elif sortBy in ["portsummaryid", "chainname", "tokenid", "name", "tokenage", "mcap", "avgprice", "smartbalance"]:
            sort_field = f"p.{sortBy}"
            
        query += f" ORDER BY {sort_field} {sortOrder.upper()}"
        
        return query, params
    
    def _process_token_data(self, cursor, tokens) -> List[Dict[str, Any]]:
        """
        Process raw token data from database query into structured dictionaries.
        
        Args:
            cursor: Database cursor
            tokens: Raw token data from database query
            
        Returns:
            List of processed token data dictionaries
        """
        superPortReportData = []
        for token in tokens:
            tokenData = {
                'portsummaryid': token[0],
                'chainname': token[1],
                'tokenid': token[2],
                'name': token[3],
                'tokenage': float(token[4]) if token[4] else None,
                'mcap': float(token[5]) if token[5] else None,
                'avgprice': float(token[6]) if token[6] else None,
                'smartbalance': float(token[7]) if token[7] else None,
                'attention_status': token[8],
                'attention_count': token[9],
                'total_wallets': token[10],
            }
            
            # Get wallet categories data for this token
            walletCategories = self._getWalletCategoriesForToken(cursor, token[2])
            tokenData.update(walletCategories)
            
            superPortReportData.append(tokenData)
            
        return superPortReportData
    
    def _getWalletCategoriesForToken(self, cursor, tokenId: str) -> Dict[str, Any]:
        """
        Get wallet investment data categorized by PNL for a token.
        
        Categories:
        1. 0-300K
        2. 300K-1M
        3. >1M
        
        For each category, calculate:
        1. Wallets that invested but haven't taken anything out
        2. Wallets that invested and taken out ≤30% of investment
        3. Wallets that invested and taken out >30% of investment
        
        Args:
            cursor: Database cursor
            tokenId: Token ID to analyze
            
        Returns:
            Dictionary with wallet categories data
        """
        # Get all active wallets for this token with investment data
        cursor.execute("""
            SELECT 
                wi.walletaddress,
                wi.totalinvestedamount,
                wi.amounttakenout,
                COALESCE(sm.profitandloss, '0') as pnl
            FROM walletsinvested wi
            LEFT JOIN smartmoneywallets sm ON wi.walletaddress = sm.walletaddress
            WHERE wi.tokenid = ? AND wi.status = 1
        """, (tokenId,))
        
        wallets = cursor.fetchall()
        
        # Initialize result structure
        result = {
            # PNL category 1: 0-300K
            'pnl_category_1_count': 0,
            'pnl_category_1_no_withdrawal_count': 0,
            'pnl_category_1_no_withdrawal_total': 0,
            'pnl_category_1_no_withdrawal_taken_out': 0,
            'pnl_category_1_partial_withdrawal_count': 0,
            'pnl_category_1_partial_withdrawal_total': 0,
            'pnl_category_1_partial_withdrawal_taken_out': 0,
            'pnl_category_1_significant_withdrawal_count': 0,
            'pnl_category_1_significant_withdrawal_total': 0,
            'pnl_category_1_significant_withdrawal_taken_out': 0,
            
            # PNL category 2: 300K-1M
            'pnl_category_2_count': 0,
            'pnl_category_2_no_withdrawal_count': 0,
            'pnl_category_2_no_withdrawal_total': 0,
            'pnl_category_2_no_withdrawal_taken_out': 0,
            'pnl_category_2_partial_withdrawal_count': 0,
            'pnl_category_2_partial_withdrawal_total': 0,
            'pnl_category_2_partial_withdrawal_taken_out': 0,
            'pnl_category_2_significant_withdrawal_count': 0,
            'pnl_category_2_significant_withdrawal_total': 0,
            'pnl_category_2_significant_withdrawal_taken_out': 0,
            
            # PNL category 3: >1M
            'pnl_category_3_count': 0,
            'pnl_category_3_no_withdrawal_count': 0,
            'pnl_category_3_no_withdrawal_total': 0,
            'pnl_category_3_no_withdrawal_taken_out': 0,
            'pnl_category_3_partial_withdrawal_count': 0,
            'pnl_category_3_partial_withdrawal_total': 0,
            'pnl_category_3_partial_withdrawal_taken_out': 0,
            'pnl_category_3_significant_withdrawal_count': 0,
            'pnl_category_3_significant_withdrawal_total': 0,
            'pnl_category_3_significant_withdrawal_taken_out': 0,
        }
        
        # Process each wallet
        for wallet in wallets:
            wallet_address = wallet[0]
            total_invested = self._to_decimal(wallet[1])
            amount_taken_out = self._to_decimal(wallet[2])
            pnl = self._to_decimal(wallet[3])
            
            # Skip wallets with no investment data
            if total_invested <= 0:
                continue
                
            # Determine PNL category
            pnl_category = 1  # Default: 0-300K
            if pnl > 1000000:  # >1M
                pnl_category = 3
            elif pnl > 300000:  # 300K-1M
                pnl_category = 2
                
            # Update category count
            result[f'pnl_category_{pnl_category}_count'] += 1
            
            # Determine withdrawal status
            withdrawal_percentage = 0
            if total_invested > 0:
                withdrawal_percentage = (amount_taken_out / total_invested) * 100
                
            if amount_taken_out <= 0:
                # No withdrawal
                result[f'pnl_category_{pnl_category}_no_withdrawal_count'] += 1
                result[f'pnl_category_{pnl_category}_no_withdrawal_total'] += total_invested
                result[f'pnl_category_{pnl_category}_no_withdrawal_taken_out'] += 0  # By definition, no amount taken out
            elif withdrawal_percentage <= 30:
                # Partial withdrawal (≤30%)
                result[f'pnl_category_{pnl_category}_partial_withdrawal_count'] += 1
                result[f'pnl_category_{pnl_category}_partial_withdrawal_total'] += total_invested
                result[f'pnl_category_{pnl_category}_partial_withdrawal_taken_out'] += amount_taken_out
            else:
                # Significant withdrawal (>30%)
                result[f'pnl_category_{pnl_category}_significant_withdrawal_count'] += 1
                result[f'pnl_category_{pnl_category}_significant_withdrawal_total'] += total_invested
                result[f'pnl_category_{pnl_category}_significant_withdrawal_taken_out'] += amount_taken_out
        
        return result
    
    def _to_decimal(self, value: Any) -> Decimal:
        """
        Convert a value to Decimal, handling None and invalid values.
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal value, or 0 if conversion fails
        """
        if value is None:
            return Decimal('0')
            
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return Decimal('0')

    def filterTokensByWalletBreakdown(self, tokens, category=None, type_filter=None, min_wallets=0, min_amount=0) -> List[Dict[str, Any]]:
        """
        Filter tokens based on wallet category, type, count, and invested amount.
        This is a post-processing filter applied after the database query.
        
        Args:
            tokens: List of token data to filter
            category: Wallet category (0-300K, 300K-1M, >1M)
            type_filter: Wallet type filter (no-selling, <30%, >30%)
            min_wallets: Minimum number of wallets required
            min_amount: Minimum amount invested
            
        Returns:
            Filtered list of tokens
        """
        filtered_tokens = []
        
        # Skip filtering if no filters are set
        if not category and not type_filter and min_wallets <= 0 and min_amount <= 0:
            return tokens
            
        # Map category to the appropriate property access
        category_map = {
            "0-300K": "cat1",
            "300K-1M": "cat2",
            ">1M": "cat3"
        }
        
        # Map type to index in categoryData
        type_map = {
            "no-selling": 0,  # No Selling
            "<30%": 1,        # < 30%
            ">30%": 2         # > 30%
        }
        
        cat_key = category_map.get(category)
        type_idx = type_map.get(type_filter)
        
        for token in tokens:
            # Prepare wallet data structure for filtering
            
            # Prepare wallet data as in renderWalletCategories function
            # Ensure all values are properly converted to numbers and handle None values
            categoryData = [
                {
                    "name": "No Selling",
                    "cat1": {
                        "count": self._to_decimal(token.get("pnl_category_1_no_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_1_no_withdrawal_total", 0))
                    },
                    "cat2": {
                        "count": self._to_decimal(token.get("pnl_category_2_no_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_2_no_withdrawal_total", 0))
                    },
                    "cat3": {
                        "count": self._to_decimal(token.get("pnl_category_3_no_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_3_no_withdrawal_total", 0))
                    }
                },
                {
                    "name": "< 30%",
                    "cat1": {
                        "count": self._to_decimal(token.get("pnl_category_1_partial_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_1_partial_withdrawal_total", 0))
                    },
                    "cat2": {
                        "count": self._to_decimal(token.get("pnl_category_2_partial_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_2_partial_withdrawal_total", 0))
                    },
                    "cat3": {
                        "count": self._to_decimal(token.get("pnl_category_3_partial_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_3_partial_withdrawal_total", 0))
                    }
                },
                {
                    "name": "> 30%",
                    "cat1": {
                        "count": self._to_decimal(token.get("pnl_category_1_significant_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_1_significant_withdrawal_total", 0))
                    },
                    "cat2": {
                        "count": self._to_decimal(token.get("pnl_category_2_significant_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_2_significant_withdrawal_total", 0))
                    },
                    "cat3": {
                        "count": self._to_decimal(token.get("pnl_category_3_significant_withdrawal_count", 0)),
                        "amount": self._to_decimal(token.get("pnl_category_3_significant_withdrawal_total", 0))
                    }
                }
            ]
            
            # Apply filters
            include_token = True
            
            # If both category and type are specified
            if category and type_filter and type_idx is not None and cat_key:
                wallet_count = categoryData[type_idx][cat_key]["count"]
                wallet_amount = categoryData[type_idx][cat_key]["amount"]
                
                if wallet_count < min_wallets:
                    include_token = False
                if min_amount > 0 and wallet_amount < self._to_decimal(min_amount):
                    include_token = False
            
            # If only category is specified
            elif category and cat_key:
                # Sum up wallets across all types for this category
                total_count = sum(data[cat_key]["count"] for data in categoryData)
                total_amount = sum(data[cat_key]["amount"] for data in categoryData)
                
                if total_count < min_wallets:
                    include_token = False
                if min_amount > 0 and total_amount < self._to_decimal(min_amount):
                    include_token = False
            
            # If only type is specified
            elif type_filter and type_idx is not None:
                # Sum up wallets across all categories for this type
                total_count = sum(categoryData[type_idx][cat]["count"] for cat in ["cat1", "cat2", "cat3"])
                total_amount = sum(categoryData[type_idx][cat]["amount"] for cat in ["cat1", "cat2", "cat3"])
                
                if total_count < min_wallets:
                    include_token = False
                if min_amount > 0 and total_amount < self._to_decimal(min_amount):
                    include_token = False
            
            # If only min_wallets or min_amount is specified
            elif min_wallets > 0 or min_amount > 0:
                # Sum up all wallets across all categories and types
                total_count = sum(data[cat]["count"] for data in categoryData for cat in ["cat1", "cat2", "cat3"])
                total_amount = sum(data[cat]["amount"] for data in categoryData for cat in ["cat1", "cat2", "cat3"])
                
                if total_count < min_wallets:
                    include_token = False
                if min_amount > 0 and total_amount < self._to_decimal(min_amount):
                    include_token = False
            
            if include_token:
                filtered_tokens.append(token)
            
        return filtered_tokens 