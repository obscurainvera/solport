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
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; csrftoken=5TFpZBUcgzZrzcvSJMwPcgCcOVi5yRPL; sessionid=gkf2pkg5kijkfaybcigkgquynbahfzia; _ga_30LVG9BH2W=GS1.1.1742499607.238.0.1742499607.0.0.0; _ga_BRMXHSC2T7=GS1.1.1742499607.198.0.1742499607.0.0.0; _ga_QSLT10C1WE=GS1.1.1742499607.71.0.1742499607.0.0.0; _ga_D6FYDK42KW=GS1.1.1742528316.563.0.1742528316.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; cf_clearance=evRbHKORbkzX2VPgQMT47BLJcdPH7.nSbo.p9B5Q5Ew-1742528360-1.2.1.1-ZVXvdMnbGJwiy7RYn5f8gchBy8yyaQoW24Z_V76L6nhYDD.0b4xxBKIX3ptFKZBKIytUq19ovTmDyhAIC7qrVjCdteEt3zZhfT.foxQkINcZ18ESVNud9Ysma3DbsWLm0m1xSFgHYU9TVrwW_s6tci5Dr.2l9hUcIdYwg34u1ZWShDAj21L5EyItxKMHUqJF0A2SM7uRgzGdaFTXy6gQkp8bQAYTQ4nZdQKsbFvPkEQXFkwdM5XhKEWLuPEvdka2WWUEnCuQ9virnthLeedQeGRuCrjmD9c49D6oxoC4Oe5cwR9BnencrG8CXycf48kg0_PDO.ncrljEysrwr1_risCyQMpK86n6yu1dQORETy4bbyHkLWQEYkc9oplBj.oi; _ga_PS3V7B7KV0=GS1.1.1742528360.213.0.1742528365.0.0.0'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; csrftoken=A5UKYKMCXslzw6dLztJ8M29j4gaBxfKe; _ga_D6FYDK42KW=GS1.1.1740619301.510.0.1740619301.0.0.0; _ga_30LVG9BH2W=GS1.1.1740621963.213.1.1740623433.0.0.0; _ga_BRMXHSC2T7=GS1.1.1740621963.173.1.1740623433.0.0.0; _ga_QSLT10C1WE=GS1.1.1740621963.46.1.1740623433.0.0.0'



COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 22)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 22)
        }
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 3, 22)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 20)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 9)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 19)
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
