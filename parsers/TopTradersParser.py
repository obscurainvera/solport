"""
Parser for top traders API response
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pytz
import re
from logs.logger import get_logger

logger = get_logger(__name__)

class TopTradersParser:
    """Parser for top traders API response"""
    
    @staticmethod
    def parseResponse(response_data: Dict[str, Any]) -> List[Dict]:
        """
        Parse the API response into a list of trader dictionaries
        
        Args:
            response_data: Raw API response data
            
        Returns:
            List[Dict]: List of parsed trader data
        """
        try:
            if not response_data or 'data' not in response_data:
                logger.error("Invalid response data format")
                return []
                
            # Get current time in IST for created_at and updated_at
            ist_timezone = pytz.timezone('Asia/Kolkata')
            current_time = datetime.now(ist_timezone).strftime('%Y-%m-%d %H:%M:%S')
                
            traders = []
            for item in response_data['data']:
                try:
                    trader = {
                        'walletaddress': item.get('wallet', '').strip(),
                        'tokenid': item.get('token_id', '').strip(),
                        'tokenname': item.get('tokenname', '').strip(),
                        'chain': item.get('chain_org', '').strip().lower(),
                        'pnl': TopTradersParser._parse_decimal(item.get('pnl')),
                        'roi': TopTradersParser._parse_decimal(item.get('roi')),
                        'avgentry': TopTradersParser._parse_decimal(item.get('avgentry')),
                        'avgexit': TopTradersParser._parse_decimal(item.get('avgexit')),
                        'startedat': item.get('start_period'),
                        'createdat': current_time,
                        'updatedat': current_time
                    }
                    
                    # Convert startedat to proper datetime format if it exists
                    if trader['startedat']:
                        try:
                            dt = datetime.strptime(trader['startedat'], '%Y-%m-%d %H:%M:%S')
                            trader['startedat'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Invalid date format for startedat: {trader['startedat']}")
                            trader['startedat'] = None
                    
                    traders.append(trader)
                except Exception as e:
                    logger.error(f"Error parsing trader data: {e}")
                    continue
                    
            return traders
            
        except Exception as e:
            logger.error(f"Error in parse_response: {e}")
            return []
            
    @staticmethod
    def _parse_decimal(value: Any) -> float:
        """
        Safely parse a value to float for SQLite compatibility, handling various input formats
        including subscript characters
        
        Args:
            value: The value to parse (could be string, float, int, etc.)
            
        Returns:
            float: The parsed float value or 0.0 if parsing fails
        """
        if value is None or value == '':
            return 0.0
            
        try:
            # Handle string with currency symbols, commas, etc.
            if isinstance(value, str):
                # Remove currency symbols, commas, and spaces
                cleaned = value.strip().replace('$', '').replace(',', '').replace(' ', '')
                
                # Handle percentage values
                if '%' in cleaned:
                    cleaned = cleaned.replace('%', '')
                    return float(cleaned) / 100
                
                # Handle empty or invalid strings
                if not cleaned or cleaned.lower() in ['na', 'n/a', '-']:
                    return 0.0
                
                # Handle subscript characters (like ₅ in 0.₅734)
                subscript_map = {'₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4', 
                                 '₅': '5', '₆': '6', '₇': '7', '₈': '8', '₉': '9'}
                
                for subscript, digit in subscript_map.items():
                    cleaned = cleaned.replace(subscript, digit)
                
                return float(cleaned)
                
            # Handle numeric types
            return float(value)
            
        except (ValueError, TypeError) as e:
            logger.warning(f"Could not parse value '{value}' as float: {e}")
            return 0.0
