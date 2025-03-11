"""
Example usage of the notification framework
"""
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.operations.sqlite_handler import SQLitePortfolioDB
from framework.notificationframework.NotificationManager import NotificationManager
from framework.notificationframework.NotificationEnums import NotificationSource, ChatGroup
from logs.logger import get_logger

logger = get_logger(__name__)

def main():
    """Main function demonstrating notification framework usage"""
    try:
        # Initialize database
        db = SQLitePortfolioDB()
        
        # Create notification manager
        notificationManager = NotificationManager(db)
        
        # Example 1: Send a simple message with automatic chat group selection
        success = notificationManager.sendMessage(
            source=NotificationSource.SYSTEM,
            content="Hello from the notification framework!"
        )
        logger.info(f"Example 1 result: {success}")
        
        # Example 2: Send a message to a specific chat group
        success = notificationManager.sendMessage(
            source=NotificationSource.ATTENTION,
            content="Important attention alert!",
            chatGroup=ChatGroup.ATTENTION_CHAT
        )
        logger.info(f"Example 2 result: {success}")
        
        # Example 3: Send a message with a button
        button = notificationManager.createButton(
            text="Visit DexScreener",
            url="https://dexscreener.com/"
        )
        
        success = notificationManager.sendMessage(
            source=NotificationSource.VOLUME,
            content="New high volume token detected!",
            chatGroup=ChatGroup.VOLUME_CHAT,
            buttons=[button]
        )
        logger.info(f"Example 3 result: {success}")
        
        # Example 4: Send a message with multiple buttons
        button1 = notificationManager.createButton(
            text="Token Info",
            url="https://dexscreener.com/solana/sampletoken"
        )
        
        button2 = notificationManager.createButton(
            text="Solscan",
            url="https://solscan.io/token/sampletoken"
        )
        
        success = notificationManager.sendMessage(
            source=NotificationSource.PORTSUMMARY,
            content="<b>New token added to portfolio:</b>\nName: Sample Token\nPrice: $0.0012\nMarket Cap: $1.2M",
            chatGroup=ChatGroup.PORTSUMMARY_CHAT,
            buttons=[button1, button2]
        )
        logger.info(f"Example 4 result: {success}")
        
        # Example 5: Process any pending notifications
        sent_count = notificationManager.processPendingNotifications()
        logger.info(f"Processed {sent_count} pending notifications")
        
        # Example 6: Retry failed notifications
        retry_count = notificationManager.retryFailedNotifications()
        logger.info(f"Retried {retry_count} failed notifications")
        
    except Exception as e:
        logger.error(f"Error in notification example: {e}")
    finally:
        # Close database connection
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main() 