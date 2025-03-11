"""
Example usage of the notification framework for token notifications

Note: Before running this example, make sure to:
1. Store the Telegram bot token in the database using the API_KEY credential type
2. Store the Telegram chat ID in the database using the CHAT_ID credential type

You can use the setup_telegram_credentials.py example to do this.
"""
import sys
import os
from decimal import Decimal

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.operations.sqlite_handler import SQLitePortfolioDB
from framework.notificationframework.NotificationManager import NotificationManager
from framework.notificationframework.NotificationEnums import NotificationSource, ChatGroup
from logs.logger import get_logger

logger = get_logger(__name__)

def main():
    """Main function demonstrating token notification usage"""
    try:
        # Initialize database
        db = SQLitePortfolioDB()
        
        # Create notification manager
        notificationManager = NotificationManager(db)
        
        # Example 1: Creating and sending a token notification using TokenNotificationContent
        token_content = notificationManager.createTokenContent(
            subject="Token Holdings Grt than 100K\nYoung Token",
            contractAddress="FtUEW73K6vEYHfbkfpdbZFwpxgQar2HipGdbut",
            symbol="tttcoin",
            chain="sol",
            tokenName="Ehpump",
            currentPrice=Decimal("0.002063"),
            balanceUsd=Decimal("85650"),  # Will be formatted as $85.65K
            liquidity=Decimal("175260"),  # Will be formatted as $175.26K
            fullyDilutedValue=Decimal("2060000"),  # Will be formatted as $2.06M
            holderCount=4,
            txnChartUrl="https://example.com/txnchart",
            dexScreenerUrl="https://dexscreener.com/"
        )
        
        success = notificationManager.sendTokenNotification(
            source=NotificationSource.PORTSUMMARY,
            tokenContent=token_content,
            chatGroup=ChatGroup.PORTSUMMARY_CHAT
        )
        logger.info(f"Example 1 result: {success}")
        
        # Example 2: Sending a token notification using a dictionary
        token_dict = {
            "subject": "New Important Token Alert",
            "contractAddress": "Gc75vQziKGNK4jD6Z6UfAEcYnNbbt3ovyiM6Tcp6TaTS",
            "symbol": "PUMP",
            "chain": "sol",
            "tokenName": "PumpCoin",
            "currentPrice": "0.0045",  # Will be converted to Decimal
            "balanceUsd": "152000",  # Will be converted to Decimal and formatted as $152.00K
            "liquidity": "320000",  # Will be converted to Decimal and formatted as $320.00K
            "fullyDilutedValue": "4500000",  # Will be converted to Decimal and formatted as $4.50M
            "holderCount": "12",  # Will be converted to int
            "txnChartUrl": "https://solscan.io/token/Gc75vQziKGNK4jD6Z6UfAEcYnNbbt3ovyiM6Tcp6TaTS#txs",
            "dexScreenerUrl": "https://dexscreener.com/solana/Gc75vQziKGNK4jD6Z6UfAEcYnNbbt3ovyiM6Tcp6TaTS"
        }
        
        success = notificationManager.sendTokenNotification(
            source=NotificationSource.ATTENTION,
            tokenContent=token_dict,
            chatGroup=ChatGroup.ATTENTION_CHAT
        )
        logger.info(f"Example 2 result: {success}")
        
        # Note: The chat ID for each notification is directly retrieved from the
        # database using the CHAT_ID credential type. The implementation does not
        # require mapping between ChatGroup and chat IDs - it simply uses the
        # stored chat ID in the database.
        
    except Exception as e:
        logger.error(f"Error in token notification example: {e}")
    finally:
        # Close database connection
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main() 