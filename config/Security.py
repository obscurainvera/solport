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
CHAINEDGE_COOKIE = '_ga=GA1.1.60016713.1730025993; __stripe_mid=86d76ae8-5f87-4e05-8e8e-c5eaf0b99f8895f778; _ga_D6FYDK42KW=deleted; _ga_30LVG9BH2W=GS1.1.1743076739.262.1.1743076755.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743076739.222.1.1743076755.0.0.0; _ga_QSLT10C1WE=GS1.1.1743076739.95.1.1743076755.0.0.0; csrftoken=JyNsRiFe42faLsaT253vjJegLanYDKP7; sessionid=crmghucb2qesjm7puxhkjp4p1atd5885; _ga_D6FYDK42KW=GS1.1.1743132922.599.1.1743132928.0.0.0'
SOLSCAN_COOKIE ='_ga=GA1.1.1697493596.1730686033; cf_clearance=arUFVu41lqaSJgjeEV1S3.QAOrBonwJgvulS0AD2_Sc-1743132979-1.2.1.1-Vj7Yz9njGvl1tnDSews5Piy9pePuA81quIKNAG3ApTW9CZS7fDZIKZqeJiG1g.p6yttzUbKIxtM8_AQtIe4AAX5d.MjJ19NNY56e5uGtgQdHS4I1kar6EoUQBAcV4Er0BdJ_Iikbp3n6Buufbqs_gx956HjhFYZppj7CEa5ktq0SoI2aY9ass36LkdtlsE6QGXLi4qfbj3etBgdQEnpI_l3xgeVW16g0dh_kNb9oHGYJpApjqaOCllMH7IA7g.ZcCtT6QtL2lw5BVZXJ8ExWrReUFiCA6D3i78y8Vodc1pkIa6JGRPh1SpRA6DW36h5pvviCSk0neJALOZYXmZinj7cNuSsOFHl23AkZpBvnByaSu_ww7XI7TQtxvHx_Rx.fV6Q0vz3VvJCVdnhIGLl0IAFX2ATPykY33PHYpnoxlQA; _ga_PS3V7B7KV0=GS1.1.1743132979.232.0.1743132987.0.0.0'
TRADING_TERMINAL_COOKIE = '_ga=GA1.1.60016713.1730025993; csrftoken=A5UKYKMCXslzw6dLztJ8M29j4gaBxfKe; _ga_D6FYDK42KW=GS1.1.1743075332.598.1.1743075352.0.0.0; _ga_30LVG9BH2W=GS1.1.1743076739.262.1.1743076755.0.0.0; _ga_BRMXHSC2T7=GS1.1.1743076739.222.1.1743076755.0.0.0; _ga_QSLT10C1WE=GS1.1.1743076739.95.1.1743076755.0.0.0'





COOKIE_MAP = {
    # Action-specific cookies
    'portfolio': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 29)
        }
    },
    'walletsinvested': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 29)
        }
    },
    'solscan': {
        SOLSCAN_COOKIE: {
            'expiry': datetime(2025, 3, 29)
        }
    },
    'smartmoneywallets': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 29)
        }
    },
    'smwallettoppnltoken': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 25)
        }
    },
    'attention': {
        CHAINEDGE_COOKIE: {
            'expiry': datetime(2025, 3, 29)
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
