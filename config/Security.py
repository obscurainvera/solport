"""
Security-sensitive configurations
- Cookie management
- Authentication tokens
- Rate limiting settings
- Service credentials
"""

from datetime import datetime
import json
from typing import Dict, Tuple, List

# Auth Token Configuration
ACCESS_TOKEN_EXPIRY_MINUTES = 15
REFRESH_TOKEN_EXPIRY_HOURS = 12
TOKEN_REFRESH_BUFFER_MINUTES = 1
RELOGIN_BUFFER_MINUTES = 5

# Define the Chainedge cookie
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; csrftoken=Er5AXkgzSRdP1gAPSFQJ9UDZ5ioZk9n6; sessionid=skrdq3stou4wro3a9evwuqwtylawv6p3; _ga_30LVG9BH2W=GS1.1.1742745195.240.1.1742749845.0.0.0; _ga_BRMXHSC2T7=GS1.1.1742745195.200.1.1742749845.0.0.0; _ga_QSLT10C1WE=GS1.1.1742745195.73.1.1742749845.0.0.0; _ga_D6FYDK42KW=GS1.1.1742782479.575.1.1742782489.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; _ga_PS3V7B7KV0=GS1.1.1742782518.222.0.1742782518.0.0.0; cf_clearance=STDWXppoAaOpPR0zu8F3BYHU0btLOlvqwidaDa9mL4Y-1742792051-1.2.1.1-eWHpUDnHAhFeQe532xFSURLIIEd_ZMk8SlulvpwgrgSrSGFbeCK76RWsW15y.7moH3lbg4_5UTt68wcufbMGaHUWLpsZAg9EvKoNHZbMDQTNGo15Nls4qU9UUtTONnm7woPuB30wCzJ4_FsM1kMp9nsOb8nDdD7usxNh8fd0hQnz8lm_UwpdibKLaKlNVnzQiIztWQL2Wg1I2lWdCU2jigH9UnWGd6YOxMYxqbYssE6X2f4B50.Dr4Ij9nPKZT2u8zxn9G9Ne1BtHB1wyA2xQbuyalhrcUgnOeFkbT9tW_fmKEAwyrZZQnNxebCGONHP7qCm1jkdAn3GZfVgjKb2R0l2K255D1oa2bGYmkUBVlqrUTFlFXYdNr_JE2_wzvAlvLH8qcgJNqvnkrM_bu_xaCPQxcvU5DDlrMDlOREYwcg'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; csrftoken=A5UKYKMCXslzw6dLztJ8M29j4gaBxfKe; _ga_D6FYDK42KW=GS1.1.1742813046.582.1.1742813141.0.0.0; _ga_30LVG9BH2W=GS1.1.1742817171.246.0.1742817172.0.0.0; _ga_BRMXHSC2T7=GS1.1.1742817171.206.0.1742817172.0.0.0; _ga_QSLT10C1WE=GS1.1.1742817171.79.0.1742817172.0.0.0'


COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'volumebot': {
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        },
    },
    'pumpfun': {    
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    }
}


def isValidCookie(cookie_value: str, required_action: str = None) -> bool:
    """Validate cookie in 3 steps:
    1. Check cookie exists for the required action
    2. Verify not expired
    3. Return True if all checks pass"""
    
    # 1. Check cookie exists for the action
    service = COOKIE_MAP.get(required_action, {}) if required_action else None
    if not service or cookie_value not in service:
        return False
        
    cookie_data = service[cookie_value]
    
    # 2. Check expiry time
    if datetime.now() > cookie_data.get('expiry', datetime.min):
        return False
        
    # 3. All checks passed
    return True
