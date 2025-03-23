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
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; _ga_PS3V7B7KV0=GS1.1.1742743789.220.0.1742743789.0.0.0; cf_clearance=bhxQgfs8f92ym7g8_2DIsFhxUKr.ObF.Z2a2r0HDAqk-1742743809-1.2.1.1-sDvgRGGv8vinw1KAAXfR_.PRMWMSHmuO47MUQGxyxLykg4xmZIZ4XiE.Td_CXQBCyelTMJpBiOpj9cffWq3gg0lTOBxPoFUsajJ7ytZHD3JLjTHYXAoKDhMSJ_VLS_xQjr5I_8K8if9SxP3oagqmWrsBAA_5ctWBGsnQffMCByhPlNMUo4YJOonUhLKXZ3Gk5TE0CW01HB2PXAylVzG9iaMPEwrmPRAxz2e_yrpMwJt.UlyusJRONRcc8C4jBqgCH8riH_1pKdRtgVgMrKK0r2.CVgvCH7FmXuhasdTc9elHeHRTv1VENlyvjXCGHtVXo8t70_EySGXJo2v9b6WW.Zos808iuuiZ_P1Gmbg3CuSGxFa44hGHFlnjhAWxBs0h9HgEo6WrE.t1XOwgoZ8kEYE.SSGDCoqG6y7EOhaRC4Q'
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
