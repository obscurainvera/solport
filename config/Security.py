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
CHAINEDGE_COOKIE = '_ga=GA1.1.2065912406.1746274726; csrftoken=fvwaHSxHKjmRzbVz24KIZAYdBpzOvjMM; sessionid=6mu9fxc8l2csu2vyvdvea0l2vt7rm8vw; _ga_30LVG9BH2W=GS2.1.s1746960460$o24$g1$t1746960462$j0$l0$h0; _ga_BRMXHSC2T7=GS2.1.s1746960460$o24$g1$t1746960462$j0$l0$h0; _ga_QSLT10C1WE=GS2.1.s1746960460$o24$g1$t1746960462$j0$l0$h0; _ga_D6FYDK42KW=GS2.1.s1746960526$o31$g1$t1746960615$j0$l0$h0'
SOLSCAN_COOKIE ='_ga=GA1.1.192595050.1746368440; cf_clearance=9_slBGzAdPdK3YGznWLTh1r.rWM9FF5sVXD5i.1gRDA-1746960704-1.2.1.1-dpucF8TQI5zwNSOBtcca4pNMVOIOIX27pA7yXTqj3gppJZa3fp7j4qhmRhn7SqShunCC29H44iWMH2P6rdPlym0QcC26xJ1q0n8YVjgGIkUBkHVNAqw8y27Zh9iZ2E33ggM6dqPhpZiOK3wucZNhXaurIT6pf4HPzhE7J91pFxEOabJFzf5hFUmocqZLj.ywnusB.Rk6dWBm3Oqc27XDPouxzxrHYlhaBWCumCBi2XDGIouX.y4rHmMD5MsZq9EvIi6CF8xYJG17rNCpH07G7rtXzTb5fc.iHZosrqsRPTyMR8vsq_eEwN9lkPtN8BryyJ1GBN7QxqQj4y7gv5WPAv_EqxAY5db_RNjLtBpPfXjhMUBqxEJbc1nuX_Id58ZH; _ga_PS3V7B7KV0=GS2.1.s1746960706$o19$g0$t1746960746$j0$l0$h0'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; _ga_30LVG9BH2W=deleted; _ga_QSLT10C1WE=deleted; wallet_created=true; wallet_exported=true; passkey_wallet=true; refreshToken=undefined; _ga_D6FYDK42KW=GS1.1.1743506365.611.1.1743506835.0.0.0; accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQzNTA3ODQ5LCJpYXQiOjE3NDMzMTIwODksImp0aSI6Ijg4NThlMGRiODM2NDQ4YTE4ZGYzZTcxYWUyMThmZWQwIiwidXNlcl9pZCI6MTQ2MCwid2FsbGV0X2NyZWF0ZWQiOnRydWUsIndhbGxldF9leHBvcnRlZCI6dHJ1ZSwicGFzc2tleV93YWxsZXQiOnRydWUsInJlZmVycmVyX2xpbmsiOiIiLCJyZWZlcnJlcl92YWxpZCI6ZmFsc2V9.rEnYGufiUsV2R8-yP_MBVNxTevtNk2Wc_AczMxRUAKE; _ga_30LVG9BH2W=GS1.1.1743506945.272.1.1743506952.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743506945.232.1.1743506952.0.0.0; _ga_QSLT10C1WE=GS1.1.1743506945.105.1.1743506952.0.0.0'




COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 12)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 12)
        }       
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 5, 12)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 12)
        }
    },
    'toptraders': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 12)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 4, 4)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 12)  
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
