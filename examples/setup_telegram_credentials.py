"""
Example of how to set up Telegram credentials in the database
"""
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.operations.sqlite_handler import SQLitePortfolioDB
from database.auth.ServiceCredentialsEnum import ServiceCredentials, CredentialType
from logs.logger import get_logger

logger = get_logger(__name__)

def main():
    """Set up Telegram credentials in the database"""
    try:
        # Initialize database
        db = SQLitePortfolioDB()
        
        # Add Telegram Bot Token (API Key)
        bot_token = "7993487629:AAFms9HmjAJHxFX7atlZAuHbDuH1ZfdBOoc"  # Replace with your actual bot token
        
        success = db.credentials.storeApiCredentials(
            serviceName="telegram",  # Must match the service name in ServiceCredentials enum
            apiKey=bot_token,
            apiSecret=None,
            availableCredits=None,
            metadata={"description": "Telegram Bot Token for notifications"}
        )
        
        if success:
            logger.info("Successfully stored Telegram bot token")
        else:
            logger.error("Failed to store Telegram bot token")
        
        # Add Telegram Chat ID
        chat_id = "6507732002"  # Replace with your actual chat ID
        
        # We store the chat ID as an API key with credential type CHAT_ID
        success = db.credentials.storeCredentialWithType(
            serviceName="telegram",
            credentialType=CredentialType.CHAT_ID.value,
            apiKey=chat_id,
            apiSecret=None,
            availableCredits=None,
            metadata={"description": "Telegram Chat ID for Portfolio alerts"}
        )
        
        if success:
            logger.info("Successfully stored Telegram chat ID")
        else:
            logger.error("Failed to store Telegram chat ID")
        
    except Exception as e:
        logger.error(f"Error setting up Telegram credentials: {e}")
    finally:
        # Close database connection
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main() 