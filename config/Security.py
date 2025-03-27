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
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; csrftoken=D8PPfI0qG4881oVYI8cCV8emdctpmUB6; sessionid=t1v7s5kfl1adb2wtaiycnldy4eadt2yn; _ga_30LVG9BH2W=GS1.1.1743069860.261.0.1743069860.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743069860.221.0.1743069860.0.0.0; _ga_QSLT10C1WE=GS1.1.1743069860.94.0.1743069860.0.0.0; _ga_D6FYDK42KW=GS1.1.1743069792.597.1.1743070111.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; cf_clearance=2h73fFAlFEkpP0riGxoxOtWNeRs4.L9HGRvZ85LQLHo-1743070265-1.2.1.1-xfGya8fVfCy6IJ8Y42pA.aS_Q.qBCQpmN9KGLS1RP6FAS6.lnGRsIEjkwS6LIN3A41LCHs4vGLNcUIVIPkEMeOVklhA1te7wMy1a3sAvEwarotezwnPQtOPEkz5ruAR1YOk0BBw09_5Cfy_Yr.op4ujrCIHZGPGm_KWedzjz7Ga2m81s7HdrBUGqf.BxeB5n7TGq0Nfh2F_Ta77cLnosVmBQ7HDZ.0Q.kwsg4.iYjurKHgpw1alOswa_X52ELbIJI3UweAsWfpWz319H5KFnfEwpngExYwEEpRUX5KpNMfpHUrpFR6FHmivZodSrK7m6fixTXFaP5DjAyTdFgkFFLHwXA3U5uB.McxA6XqqvFBJ5XMWGZ_np5eSVPENmnz0XOEr4GD29sYf91M.0jpTYD8x4q5UQQzMHjQKQZbzv0Sk; _ga_PS3V7B7KV0=GS1.1.1743069789.231.1.1743070355.0.0.0'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; csrftoken=A5UKYKMCXslzw6dLztJ8M29j4gaBxfKe; _ga_D6FYDK42KW=GS1.1.1743021911.594.1.1743021989.0.0.0; _ga_30LVG9BH2W=GS1.1.1743021915.258.1.1743022064.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743021915.218.1.1743022064.0.0.0; _ga_QSLT10C1WE=GS1.1.1743021915.91.1.1743022064.0.0.0'
COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 28)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 28)
        }
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 3, 28)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 26)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 28)
        }
    },
    'volumebot': {
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 3, 26)
        },
    },
    'pumpfun': {    
        TRADING_TERMINAL_COOKIE: {
            'expiry': datetime(2025, 3, 26)
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
