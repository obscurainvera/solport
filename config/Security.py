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
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; csrftoken=y5DJ5mM0eDvvNb2CKdD5m53bOJkwOYms; sessionid=un2tyneefkhkr9kze6zs47mt32nocw7p; _ga_30LVG9BH2W=GS1.1.1746105089.392.0.1746105089.0.0.0; _ga_BRMXHSC2T7=GS1.1.1746105089.352.0.1746105089.0.0.0; _ga_QSLT10C1WE=GS1.1.1746105089.225.0.1746105089.0.0.0; _ga_D6FYDK42KW=GS1.1.1746105063.771.1.1746105187.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; _ga_PS3V7B7KV0=GS1.1.1746075759.308.0.1746075759.0.0.0; cf_clearance=0za0WnMlMvQXyENYCJ9tkSh2KgqrC_ZnWPxX7ofzJa8-1746105247-1.2.1.1-GhbwZFoxT_rt7CDP0SeaJI5HcuV0DlBvOiFjhBtgYgSHmxZz13.C4rj1_Zsp.3EAjSfz8cwTXlVVK.WUgykKHsnERKBx9DSUKoE5Ohme_LYHGsF6kx8kNoLDzHkc3GV2wbXn3y6CELMUNa2oIcsnjxQAnsZ7doTvYyPM.bgQ7IO0Pv7w8iHvwYkqaHp9SJvihUgXrQkggK3rfHzpHc62HN9PeYEeAnVneSl6SbaGAt8DdYggEFkNP6vbwiuA8CdLtOoGJb1ys0EkxR2zi6T2s3aTDu_WUE69B8rJ5Y.pyblj7wn.mcuRXzb7XLnYK4uzz5VNk79oKyUs1A4M2vhUbZQl.67rF6fKhsOrQpWFCquou_ASukxuhceZVxG1gJVH'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; _ga_30LVG9BH2W=deleted; _ga_QSLT10C1WE=deleted; wallet_created=true; wallet_exported=true; passkey_wallet=true; refreshToken=undefined; _ga_D6FYDK42KW=GS1.1.1743506365.611.1.1743506835.0.0.0; accessToken=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQzNTA3ODQ5LCJpYXQiOjE3NDMzMTIwODksImp0aSI6Ijg4NThlMGRiODM2NDQ4YTE4ZGYzZTcxYWUyMThmZWQwIiwidXNlcl9pZCI6MTQ2MCwid2FsbGV0X2NyZWF0ZWQiOnRydWUsIndhbGxldF9leHBvcnRlZCI6dHJ1ZSwicGFzc2tleV93YWxsZXQiOnRydWUsInJlZmVycmVyX2xpbmsiOiIiLCJyZWZlcnJlcl92YWxpZCI6ZmFsc2V9.rEnYGufiUsV2R8-yP_MBVNxTevtNk2Wc_AczMxRUAKE; _ga_30LVG9BH2W=GS1.1.1743506945.272.1.1743506952.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743506945.232.1.1743506952.0.0.0; _ga_QSLT10C1WE=GS1.1.1743506945.105.1.1743506952.0.0.0'




COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 2)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 2)
        }       
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 5, 2)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 2)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 4, 4)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 5, 2)  
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
