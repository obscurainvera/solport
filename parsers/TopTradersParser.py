"""
Parser for top traders API response
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from decimal import Decimal, InvalidOperation
import pytz
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
                        'startedat': item.get('start_period')
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
    def _parse_decimal(value: Any) -> Optional[Decimal]:
        """
        Safely parse a value to Decimal, handling various input formats
        
        Args:
            value: The value to parse (could be string, float, int, etc.)
            
        Returns:
            Optional[Decimal]: The parsed Decimal or None if parsing fails
        """
        if value is None or value == '':
            return None
            
        try:
            # Handle string with currency symbols, commas, etc.
            if isinstance(value, str):
                # Remove currency symbols and commas
                cleaned = value.strip().replace('$', '').replace(',', '')
                return Decimal(cleaned)
            # Handle numeric types
            return Decimal(str(value))
        except (ValueError, InvalidOperation, TypeError) as e:
            logger.warning(f"Could not parse value '{value}' as Decimal: {e}")
            return None
