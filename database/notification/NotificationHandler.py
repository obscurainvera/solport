"""
Handler for notification database operations
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import json
import sqlite3
import pytz
from database.operations.base_handler import BaseSQLiteHandler
from database.operations.schema import Notification, NotificationButton
from framework.notificationframework.NotificationEnums import NotificationStatus
from logs.logger import get_logger

logger = get_logger(__name__)

class NotificationHandler(BaseSQLiteHandler):
    """
    Handler for notification database operations
    """
    
    def __init__(self, conn_manager):
        """Initialize with connection manager"""
        super().__init__(conn_manager)
        self.tableName = 'notification'
        self._ensureTableExists()
    
    def _ensureTableExists(self) -> None:
        """Ensure the notification table exists"""
        with self.transaction() as cursor:
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.tableName} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    chatgroup TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT '{NotificationStatus.PENDING.value}',
                    servicetype TEXT,
                    errordetails TEXT,
                    buttons TEXT,
                    createdat TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updatedat TIMESTAMP,
                    sentat TIMESTAMP
                )
            ''')
            
            # Create index for faster queries
            cursor.execute(f'''
                CREATE INDEX IF NOT EXISTS idx_{self.tableName}_status
                ON {self.tableName} (status)
            ''')
    
    def createNotification(self, notification: Notification) -> Optional[Notification]:
        """
        Create a new notification record
        
        Args:
            notification: Notification object to save
            
        Returns:
            Optional[Notification]: Saved notification with ID or None if failed
        """
        try:
            with self.transaction() as cursor:
                now = self.getCurrentIstTime()
                
                # Set timestamps
                notification.createdat = now
                notification.updatedat = now
                
                # Serialize buttons to JSON if present
                buttons_json = json.dumps([{"text": btn.text, "url": btn.url} for btn in notification.buttons]) if notification.buttons else None
                
                # Insert into database
                cursor.execute(f'''
                    INSERT INTO {self.tableName} 
                    (source, chatgroup, content, status, servicetype, errordetails, buttons, createdat, updatedat, sentat)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    notification.source,
                    notification.chatgroup,
                    notification.content,
                    notification.status,
                    notification.servicetype,
                    notification.errordetails,
                    buttons_json,
                    notification.createdat,
                    notification.updatedat,
                    notification.sentat
                ))
                
                # Get the ID of the inserted row
                notification.id = cursor.lastrowid
                
                return notification
                
        except Exception as e:
            logger.error(f"Failed to create notification: {e}")
            return None
    
    def updateNotification(self, notification: Notification) -> bool:
        """
        Update an existing notification record
        
        Args:
            notification: Notification object to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            if not notification.id:
                logger.error("Cannot update notification without an ID")
                return False
            
            with self.transaction() as cursor:
                # Update timestamp
                notification.updatedat = self.getCurrentIstTime()
                
                # Serialize buttons to JSON if present
                buttons_json = json.dumps([{"text": btn.text, "url": btn.url} for btn in notification.buttons]) if notification.buttons else None
                
                # Update record
                cursor.execute(f'''
                    UPDATE {self.tableName}
                    SET source = ?,
                        chatgroup = ?,
                        content = ?,
                        status = ?,
                        servicetype = ?,
                        errordetails = ?,
                        buttons = ?,
                        updatedat = ?,
                        sentat = ?
                    WHERE id = ?
                ''', (
                    notification.source,
                    notification.chatgroup,
                    notification.content,
                    notification.status,
                    notification.servicetype,
                    notification.errordetails,
                    buttons_json,
                    notification.updatedat,
                    notification.sentat,
                    notification.id
                ))
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to update notification: {e}")
            return False
    
    def getNotificationById(self, notificationId: int) -> Optional[Notification]:
        """
        Get a notification by ID
        
        Args:
            notificationId: ID of the notification to retrieve
            
        Returns:
            Optional[Notification]: Notification object if found, None otherwise
        """
        try:
            with self.transaction() as cursor:
                cursor.execute(f'''
                    SELECT id, source, chatgroup, content, status, servicetype, 
                           errordetails, buttons, createdat, updatedat, sentat
                    FROM {self.tableName}
                    WHERE id = ?
                ''', (notificationId,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                return self._rowToNotification(row)
                
        except Exception as e:
            logger.error(f"Failed to get notification by ID: {e}")
            return None
    
    def getPendingNotifications(self, limit: int = 10) -> List[Notification]:
        """
        Get pending notifications to be sent
        
        Args:
            limit: Maximum number of notifications to retrieve
            
        Returns:
            List[Notification]: List of pending notifications
        """
        try:
            with self.transaction() as cursor:
                cursor.execute(f'''
                    SELECT id, source, chatgroup, content, status, servicetype, 
                           errordetails, buttons, createdat, updatedat, sentat
                    FROM {self.tableName}
                    WHERE status = ?
                    ORDER BY createdat ASC
                    LIMIT ?
                ''', (NotificationStatus.PENDING.value, limit))
                
                rows = cursor.fetchall()
                return [self._rowToNotification(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get pending notifications: {e}")
            return []
    
    def getFailedNotifications(self, limit: int = 10) -> List[Notification]:
        """
        Get failed notifications
        
        Args:
            limit: Maximum number of notifications to retrieve
            
        Returns:
            List[Notification]: List of failed notifications
        """
        try:
            with self.transaction() as cursor:
                cursor.execute(f'''
                    SELECT id, source, chatgroup, content, status, servicetype, 
                           errordetails, buttons, createdat, updatedat, sentat
                    FROM {self.tableName}
                    WHERE status = ?
                    ORDER BY updatedat DESC
                    LIMIT ?
                ''', (NotificationStatus.FAILED.value, limit))
                
                rows = cursor.fetchall()
                return [self._rowToNotification(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get failed notifications: {e}")
            return []
    
    def getNotificationsBySource(self, source: str, limit: int = 10) -> List[Notification]:
        """
        Get notifications by source
        
        Args:
            source: Source of the notifications
            limit: Maximum number of notifications to retrieve
            
        Returns:
            List[Notification]: List of notifications from the specified source
        """
        try:
            with self.transaction() as cursor:
                cursor.execute(f'''
                    SELECT id, source, chatgroup, content, status, servicetype, 
                           errordetails, buttons, createdat, updatedat, sentat
                    FROM {self.tableName}
                    WHERE source = ?
                    ORDER BY createdat DESC
                    LIMIT ?
                ''', (source, limit))
                
                rows = cursor.fetchall()
                return [self._rowToNotification(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get notifications by source: {e}")
            return []
    
    def _rowToNotification(self, row: Tuple) -> Notification:
        """
        Convert a database row to a Notification object
        
        Args:
            row: Database row tuple
            
        Returns:
            Notification: Notification object
        """
        # Parse buttons JSON
        buttons = []
        if row[7]:  # buttons field
            try:
                buttons_data = json.loads(row[7])
                buttons = [NotificationButton(text=btn["text"], url=btn["url"]) for btn in buttons_data]
            except Exception as e:
                logger.error(f"Failed to parse buttons JSON: {e}")
        
        return Notification(
            id=row[0],
            source=row[1],
            chatgroup=row[2],
            content=row[3],
            status=row[4],
            servicetype=row[5],
            errordetails=row[6],
            buttons=buttons,
            createdat=row[8] if row[8] else None,
            updatedat=row[9] if row[9] else None,
            sentat=row[10] if row[10] else None
        ) 