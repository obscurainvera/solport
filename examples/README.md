# Notification Framework Examples

This directory contains examples for using the notification framework.

## Setting Up Telegram Credentials

Before using the notification framework, you need to set up your Telegram credentials:

1. Create a Telegram bot using [BotFather](https://t.me/botfather) and get your bot token
2. Get your chat ID (you can use the [@userinfobot](https://t.me/userinfobot) or other methods)
3. Run the `setup_telegram_credentials.py` script to store these credentials in the database:

```python
python examples/setup_telegram_credentials.py
```

Make sure to replace the example bot token and chat ID with your actual credentials.

## Sending Basic Notifications

The `notification_example.py` script demonstrates how to send basic text notifications:

```python
python examples/notification_example.py
```

## Sending Token Notifications

The `token_notification_example.py` script demonstrates how to send structured token notifications:

```python
python examples/token_notification_example.py
```

## Using the Notification Framework in Your Code

To use the notification framework in your code:

```python
from database.operations.sqlite_handler import SQLitePortfolioDB
from framework.notificationframework.NotificationManager import NotificationManager
from framework.notificationframework.NotificationEnums import NotificationSource

# Initialize
db = SQLitePortfolioDB()
notificationManager = NotificationManager(db)

# For simple text notifications
notificationManager.sendMessage(
    source=NotificationSource.SYSTEM,
    content="Your notification message here"
)

# For token notifications
token_data = {
    "subject": "Token Alert",
    "contractAddress": "YourTokenAddress",
    "symbol": "TOKEN",
    "chain": "sol",
    "currentPrice": "0.0045",
    "balanceUsd": "152000",
    "liquidity": "320000",
    "fullyDilutedValue": "4500000",
    "holderCount": "12"
}

notificationManager.sendTokenNotification(
    source=NotificationSource.ATTENTION,
    tokenContent=token_data
)
```

## Chat ID Handling

The notification framework has been simplified to use a single chat ID from the credentials table. This removes the need for mapping between chat groups and chat IDs. The chat ID is stored as a credential with type `CHAT_ID` in the database.

If you need to send notifications to different chat groups, you will need to switch the chat ID credential in the database before sending or implement your own mapping functionality. 