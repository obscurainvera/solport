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
CHAINEDGE_COOKIE = '_ga=GA1.1.2065912406.1746274726; _ga_30LVG9BH2W=GS2.1.s1747706791$o53$g0$t1747706791$j0$l0$h0; _ga_BRMXHSC2T7=GS2.1.s1747706791$o53$g0$t1747706791$j0$l0$h0; _ga_QSLT10C1WE=GS2.1.s1747706791$o53$g0$t1747706791$j0$l0$h0; csrftoken=tWDzdiy9HEnEwxkWUDQIqlR4x9b6a9kG; sessionid=d0s7ytlczodktlii7cf1jf47sbqf1e5w; _ga_D6FYDK42KW=GS2.1.s1748057661$o73$g0$t1748057661$j0$l0$h0'
SOLSCAN_COOKIE ='_ga=GA1.1.192595050.1746368440; _ga_PS3V7B7KV0=GS2.1.s1747969939$o41$g1$t1747969939$j0$l0$h0; cf_clearance=WN7LC_O6_w.8hMbwqzM.K3Y3i_MG6BL_PGsM3rYpeik-1748057800-1.2.1.1-uKxWucEJ6dZQKXwzXzK8bP7kpoIhngnCj8tboJBTKgoAdoqyKRD8qbB4c3ukHFVVGtpBAZRA9anFJsDKwUCxVMLn9vNPMzyEYewHL8dUUClufC0AjCRIKvsc7aslBTgbzzSq5SFgA6ziXZ_SZN2BVBE2WJ3WdtbiPzzsw0jiw6N8qn82JSsuaivRxifhfAGAcsXdJt8yW8s8jNGZ5IbbJY5HHMq4oVjmXO_r4dJagoME_twkuELWr_WcM6WhPY.LHJg7DcMUVGux5XSEllkjnOdZPWF7TifsMuaD45sNoAiyBDYdGR5xqZ_GATgG5q4dkIyJSp2sU_In9SQLpZi9CMF_NS9LCC9yTldzyq13n5NooYMb0ys0OYP2up9.Ndw4'


TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; _ga_30LVG9BH2W=deleted; _ga_QSLT10C1WE=deleted; wallet_created=true; wallet_exported=true; passkey_wallet=true; refreshToken=undefined; _ga_D6FYDK42KW=GS1.1.1743506365.611.1.1743506835.0.0.0; accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQzNTA3ODQ5LCJpYXQiOjE3NDMzMTIwODksImp0aSI6Ijg4NThlMGRiODM2NDQ4YTE4ZGYzZTcxYWUyMThmZWQwIiwidXNlcl9pZCI6MTQ2MCwid2FsbGV0X2NyZWF0ZWQiOnRydWUsIndhbGxldF9leHBvcnRlZCI6dHJ1ZSwicGFzc2tleV93YWxsZXQiOnRydWUsInJlZmVycmVyX2xpbmsiOiIiLCJyZWZlcnJlcl92YWxpZCI6ZmFsc2V9.rEnYGufiUsV2R8-yP_MBVNxTevtNk2Wc_AczMxRUAKE; _ga_30LVG9BH2W=GS1.1.1743506945.272.1.1743506952.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743506945.232.1.1743506952.0.0.0; _ga_QSLT10C1WE=GS1.1.1743506945.105.1.1743506952.0.0.0'


date = datetime(2025, 5, 25)

COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': date
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': date
        }       
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': date
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': date
        }
    },
    'toptraders': {
        CHAINEDGE_COOKIE: {
            'expiry': date
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 4, 4)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': date
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
