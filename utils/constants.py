"""
Constants used throughout the application
"""

# Token IDs
SOL_TOKEN_ID = "So11111111111111111111111111111111111111112"
TRUMP_TOKEN_ID = "6p6xgHyF7AeE6TZkSmFsko444wqoP15icUSqi2jfGiPN"
MELANIA_TOKEN_ID = "FUAfBo2jgks6gB4Z4LfZkqSZgzNucisEHqnNebaRxM1P"
USDC_TOKEN_ID = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"

# List of token IDs to always fetch prices for
DEFAULT_TOKEN_IDS = [SOL_TOKEN_ID,TRUMP_TOKEN_ID,MELANIA_TOKEN_ID] 
# List of token IDs to exclude from wallet investement details analysis
EXCLUDE_TOKEN_IDS= [USDC_TOKEN_ID]