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
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; csrftoken=L1zjEVgJGy2TpS7AQ873G25e4fuTF0JW; sessionid=0xzlicjeqxvtspe15e6041d2yxu18v6h; _ga_30LVG9BH2W=GS1.1.1744091318.291.1.1744091597.0.0.0; _ga_BRMXHSC2T7=GS1.1.1744091318.251.1.1744091597.0.0.0; _ga_QSLT10C1WE=GS1.1.1744091318.124.1.1744091597.0.0.0; _ga_D6FYDK42KW=GS1.1.1744096911.645.0.1744096911.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; _ga_PS3V7B7KV0=GS1.1.1744101315.251.1.1744101572.0.0.0; cf_clearance=V6VmSNvbpx35G2ROyrJ6DL0j7JxC2fQfl9lXCksWbmc-1744103632-1.2.1.1-BNvN7qHXHEXIW8t60XLsuAF49.B7VLHPbww1QG3BS6kekE1Njzm2X2zxKrdlqxDkVDODCBfwgXQhAp5Y.AtaVqkFgO.j8GQBofGLxyWrCxTdzSvA3h7kWR_TVHeP3bG5kCA2mrqf07HJWtxHGmZmIl5D_ylBRuRgchLcOKYAHPYx7Cw2AOyIJvE3tko0wbz_4nFJTpucRlsEqW2_tjeCr1Gz_Vkpm.nKEFn0E5ELLxL6QFhi857dUVPbJMu88BxlTbK5jFUv6Dt61cKubwWrjIJ2BqadfCeFh_K1uvTenjWJZcfc_EOXhK3PNxIABIFWDakFOUFkcXizr0knyBVfoBLtHZVqgF3FT71rJZpNpWX_N28bsYLmM6W_yyKYUYsf'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; _ga_30LVG9BH2W=deleted; _ga_QSLT10C1WE=deleted; wallet_created=true; wallet_exported=true; passkey_wallet=true; refreshToken=undefined; _ga_D6FYDK42KW=GS1.1.1743506365.611.1.1743506835.0.0.0; accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQzNTA3ODQ5LCJpYXQiOjE3NDMzMTIwODksImp0aSI6Ijg4NThlMGRiODM2NDQ4YTE4ZGYzZTcxYWUyMThmZWQwIiwidXNlcl9pZCI6MTQ2MCwid2FsbGV0X2NyZWF0ZWQiOnRydWUsIndhbGxldF9leHBvcnRlZCI6dHJ1ZSwicGFzc2tleV93YWxsZXQiOnRydWUsInJlZmVycmVyX2xpbmsiOiIiLCJyZWZlcnJlcl92YWxpZCI6ZmFsc2V9.rEnYGufiUsV2R8-yP_MBVNxTevtNk2Wc_AczMxRUAKE; _ga_30LVG9BH2W=GS1.1.1743506945.272.1.1743506952.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743506945.232.1.1743506952.0.0.0; _ga_QSLT10C1WE=GS1.1.1743506945.105.1.1743506952.0.0.0'




COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 4, 9)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 4, 9)
        }       
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 4, 9)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 4, 5)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 4, 4)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 4, 9)  
        }
    },
    'volumebot': {
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 3, 28)
        },
    },
    'pumpfun': {    
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 3, 28)
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
