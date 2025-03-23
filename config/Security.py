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
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; _ga_30LVG9BH2W=GS1.1.1742499607.238.0.1742499607.0.0.0; _ga_BRMXHSC2T7=GS1.1.1742499607.198.0.1742499607.0.0.0; _ga_QSLT10C1WE=GS1.1.1742499607.71.0.1742499607.0.0.0; csrftoken=Er5AXkgzSRdP1gAPSFQJ9UDZ5ioZk9n6; sessionid=skrdq3stou4wro3a9evwuqwtylawv6p3; _ga_D6FYDK42KW=GS1.1.1742707212.567.1.1742708122.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; _ga_PS3V7B7KV0=GS1.1.1742731721.218.1.1742731727.0.0.0; cf_clearance=EhcuaeIxbcZYLe2ipszmGsncoX0BJ_dNC5rOCKt2gGE-1742733596-1.2.1.1-uEZ4DeRf9fiTBpWvOcG3xUpc3e_wrPL5UTzsyvmZBdzPS8ZhABVhebP4i4__K7_Kxs0zQ60pLUpXPtBviEleXLvjPFLYRLxSp1b_f14VEVWSZuq79JZCEvSnzGYIfnn2vWysPqsxiu2pSzu3YuXG_XrCeNfIv0k9Uxy_Jz3lBqNIRfaHGhgNvutTlDaqUhkwHb2e7tgDFNNujpAcoAYQWfK3l2Lc1dcP4pZ4YyyU7Xbkl.bi2X5g3G6aX8QmsmlybivBQGfE8JBSr1W3ihC2zcmEyYMX_h82_Zpnc5qEsT2fqy33nspyzjcBbXzq7vGKNVaADphkqZLq.w6KD3XuDzuAmGntCHcv0Xq.K4QwoL8egSJzhvNon_W3fHNawPdhciIAxGwkLCmQWVKTCOvyW0dCkamF2QoxptSzahsnFQU'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; csrftoken=A5UKYKMCXslzw6dLztJ8M29j4gaBxfKe; _ga_D6FYDK42KW=GS1.1.1740619301.510.0.1740619301.0.0.0; _ga_30LVG9BH2W=GS1.1.1740621963.213.1.1740623433.0.0.0; _ga_BRMXHSC2T7=GS1.1.1740621963.173.1.1740623433.0.0.0; _ga_QSLT10C1WE=GS1.1.1740621963.46.1.1740623433.0.0.0'



COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 24)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 24)
        }
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 3, 24)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 24)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 24)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 24)
        }
    },
    'volumebot': {
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 2, 2)
        },
    },
    'pumpfun': {    
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 2, 28)
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
