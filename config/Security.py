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
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; csrftoken=qrmXiqmobMY6LH5BqllB6LWZZk8AfU9E; sessionid=kobj0oi2iwz7vjxwyfed0w7nb72r94j5; _ga_30LVG9BH2W=GS1.1.1741453642.225.1.1741453642.0.0.0; _ga_BRMXHSC2T7=GS1.1.1741453642.185.1.1741453642.0.0.0; _ga_QSLT10C1WE=GS1.1.1741453642.58.1.1741453642.0.0.0; _ga_D6FYDK42KW=GS1.1.1741453627.537.1.1741453667.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; _ga_PS3V7B7KV0=GS1.1.1741847097.186.0.1741847097.0.0.0; cf_clearance=bkJbw5QzmOVrej9SkjRJDNPfIWN6Nz0B2g3Ko9ISSgY-1741857299-1.2.1.1-ZdGqKyMaTeXwqoTodLweP.F6QYYyNE2R10f0IwlvczhGOPhWt0GIOAWMLNnxxhEFk3RzRF3BUOxlDwdOj0FVX4bRxW_9FRnxLBoORt0.kJGmawFfVCdGTLABxNX6DlhxEowrQ.1ISkafP8pVcbbDRPuA82Lp1vZQy_4YMaZ5mPFdlGdrfGxMCLnXKhG4EuSUPSYcOTDTkpNZODIcZvP6hTG.jM_zb2mnrTkuzW6V3TS.F6p3_1z3y0VlcfVoEo_Ob_AzN.DYuHQKt84lv03bigguivZ2Mv9sYsLOstP___89O6FrMVSTsunDUFs8N6QmVm9CijyuSc6mAWnaAYt7PZcMdVhd0bBvmNyQoiPFICLUKK0nubJABamH25CnMSBQJLxyI4IaGarQ.9Knw0T7gnlrq93ZXPwIDzCSzQc6.lQ'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; csrftoken=A5UKYKMCXslzw6dLztJ8M29j4gaBxfKe; _ga_D6FYDK42KW=GS1.1.1740619301.510.0.1740619301.0.0.0; _ga_30LVG9BH2W=GS1.1.1740621963.213.1.1740623433.0.0.0; _ga_BRMXHSC2T7=GS1.1.1740621963.173.1.1740623433.0.0.0; _ga_QSLT10C1WE=GS1.1.1740621963.46.1.1740623433.0.0.0'



COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 9)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 9)
        }
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 3, 14)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 6)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 9)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 7)
        }
    },
    'volumebot': {
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 2, 28)
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
