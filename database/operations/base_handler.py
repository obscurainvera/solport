from database.operations.connection_manager import DatabaseConnectionManager
from typing import Optional
import sqlite3
from datetime import datetime
import pytz

class BaseSQLiteHandler:
    """
    Base class for all database handlers.
    Provides common functionality and connection management.
    
    Why needed?
    - Reduces code duplication
    - Standardizes connection handling
    - Provides common interface
    """

    def __init__(self, conn_manager: DatabaseConnectionManager):
        """
        Initializes the handler with a connection manager.
        
        Why connection manager?
        - Centralizes connection management
        - Ensures proper resource handling
        - Provides thread safety
        
        Args:
            conn_manager: Shared database connection manager instance
        """
        self.conn_manager = conn_manager

    @property
    def transaction(self):
        """
        Property to access transaction context manager.
        
        Why property?
        - Cleaner syntax
        - Encapsulates connection manager
        - Consistent interface
        
        Usage:
            with handler.transaction() as cursor:
                # perform operations
        
        Returns:
            Context manager for transactions
        """
        return self.conn_manager.transaction

    @property
    def tableLock(self):
        """
        Property to access table locking mechanism.
        
        Why property?
        - Cleaner syntax
        - Encapsulates connection manager
        - Consistent interface
        
        Usage:
            with handler.tableLock('table_name'):
                # perform thread-safe operations
        
        Returns:
            Context manager for table locks
        """
        return self.conn_manager.table_lock

    def close(self):
        """
        Closes the database connection.
        
        Why needed?
        - Proper resource cleanup
        - Releases database connections
        - Prevents resource leaks
        
        When to use:
        - Finishing operations
        - Cleanup
        - Application shutdown
        """
        self.conn_manager.close()

    @staticmethod
    def getCurrentIstTime() -> datetime:
        """Get current time in IST timezone"""
        ist = pytz.timezone('Asia/Kolkata')
        return datetime.now(ist) 