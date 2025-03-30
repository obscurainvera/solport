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
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; csrftoken=JyNsRiFe42faLsaT253vjJegLanYDKP7; sessionid=crmghucb2qesjm7puxhkjp4p1atd5885; _ga_30LVG9BH2W=GS1.1.1743311864.266.0.1743311864.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743311864.226.0.1743311864.0.0.0; _ga_QSLT10C1WE=GS1.1.1743311864.99.0.1743311864.0.0.0; _ga_D6FYDK42KW=GS1.1.1743311804.602.1.1743311957.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; cf_clearance=2BeiahqmeVR.cPVYe5tcAyRlyRNzlu.19ARkDPEKCc4-1743311987-1.2.1.1-QeXC3arQ3p1_t4vFzWKnWQRrJq.3bGRflLediw5tDzO5lq.YJeKHeTc4K9wSzB.f_2O7KAym0d8ndulew1hYdO8T3pJsbu_O_veEfR_15D.jRZonXYCRGFm1QF7n0Dm.nVPD0aUJcTjrkiGgTscoD4Lfwdtc5W5_tDViYVmS9jwX0OHyIJQuCMqhDQv3nI4JO00qQ0t3f5EOyJGxVqmwWXs_kkzY5jGxqYwnLMmhL14hERzyJaILva.9qdZJmllopscnD13ft8xsauei4I8EgZcG3sy6mKjYWwbymtc3ohSTOubHbLKAiCh1gDNnyPp5486PjX1lfdfgq38o4FKwN7xOmf61zVIPhPtYBXJC.1juciDP7bD.IhOuAElTBLJSs8Ia11DOltBblNp12ajeLFXPvUEvr3rjia0kKCUEZHY; _ga_PS3V7B7KV0=GS1.1.1743311987.234.0.1743312052.0.0.0'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; csrftoken=A5UKYKMCXslzw6dLztJ8M29j4gaBxfKe; _ga_D6FYDK42KW=GS1.1.1743311804.602.1.1743311958.0.0.0; _ga_30LVG9BH2W=GS1.1.1743311864.266.1.1743312092.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743311864.226.1.1743312092.0.0.0; _ga_QSLT10C1WE=GS1.1.1743311864.99.1.1743312092.0.0.0'




COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 31)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 31)
        }
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 3, 31)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 31)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 31)
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
