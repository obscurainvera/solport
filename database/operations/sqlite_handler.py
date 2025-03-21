from database.operations.connection_manager import DatabaseConnectionManager
from database.portsummary.PortfolioHandler import PortfolioHandler
from database.smwalletsbehaviour.SmartMoneyWalletBehaviourHandler import SmartMoneyWalletBehaviourHandler
from database.walletinvested.WalletsInvestedHandler import WalletsInvestedHandler
from database.job.job_handler import JobHandler
from database.smartmoneywallets.SmartMoneyWalletsHandler import SmartMoneyWalletsHandler
from database.smartmoneywallets.SMWalletTopPNLTokenHandler import SMWalletTopPNLTokenHandler
from database.smartmoneywallets.SmartMoneyPerformanceReportHandler import SmartMoneyPerformanceReportHandler
from database.attention.AttentionHandler import AttentionHandler
from database.volume.VolumeHandler import VolumeHandler
from database.pumpfun.PumpfunHandler import PumpFunHandler
from database.auth.TokenHandler import TokenHandler
from database.auth.CredentialsHandler import CredentialsHandler
from framework.analyticshandlers.AnalyticsHandler import AnalyticsHandler
from database.notification.NotificationHandler import NotificationHandler
from typing import Optional, Any, List, Tuple
from logs.logger import get_logger
from framework.analyticsframework.models.BaseModels import ExecutionState, BaseStrategyConfig
import sqlite3

logger = get_logger(__name__)

class SQLitePortfolioDB:
    """
    Main database facade that coordinates between different handlers.
    This class acts as a single entry point for all database operations
    while delegating the actual work to specific handlers.
    
    Key Changes from Previous Version:
    - Removed direct table operations (moved to specific handlers)
    - No direct SQL queries (delegated to handlers)
    - Simplified connection management
    - Better separation of concerns
    """
    
    _instance = None
    
    def __new__(cls, db_path: str = 'portfolio.db'):
        """
        Singleton pattern implementation to ensure only one database instance exists.
        
        Why needed:
        - Prevents multiple database connections
        - Ensures consistent state across the application
        - Manages resources efficiently
        
        Args:
            db_path: Path to SQLite database file
            
        Returns:
            SQLitePortfolioDB: Single instance of the database handler
        """
        if cls._instance is None:
            cls._instance = super(SQLitePortfolioDB, cls).__new__(cls)
            cls._instance.db_path = db_path
            cls._instance._init_handlers()
        return cls._instance

    def _init_handlers(self):
        """
        Initialize all database handlers.
        Each handler is responsible for a specific domain of database operations.
        """
        self.conn_manager = DatabaseConnectionManager(self.db_path)
        
        # Initialize handlers
        self.portfolio = PortfolioHandler(self.conn_manager)
        self.walletsInvested = WalletsInvestedHandler(self.conn_manager)
        self.job = JobHandler(self.conn_manager)
        self.smartMoneyWallets = SmartMoneyWalletsHandler(self.conn_manager)
        self.smWalletTopPNLToken = SMWalletTopPNLTokenHandler(self.conn_manager)
        self.smartMoneyPerformanceReport = SmartMoneyPerformanceReportHandler(self.conn_manager)
        self.attention = AttentionHandler(self.conn_manager)
        self.volume = VolumeHandler(self.conn_manager)
        self.pumpfun = PumpFunHandler(self.conn_manager)
        self.token = TokenHandler(self.conn_manager)
        self.credentials = CredentialsHandler(self.conn_manager)
        self.analytics = AnalyticsHandler(self.conn_manager)
        self.notification = NotificationHandler(self.conn_manager)
        self.smWalletBehaviour = SmartMoneyWalletBehaviourHandler(self.conn_manager)
        
        # Map handler names to instances for dynamic access
        self._handlers = {
            'portfolio': self.portfolio,
            'walletsInvested': self.walletsInvested,
            'job': self.job,
            'smartMoneyWallets': self.smartMoneyWallets,
            'smWalletTopPNLToken': self.smWalletTopPNLToken,
            'smartMoneyPerformanceReport': self.smartMoneyPerformanceReport,
            'attention': self.attention,
            'volume': self.volume,
            'pumpfun': self.pumpfun,
            'token': self.token,
            'credentials': self.credentials,
            'analytics': self.analytics,
            'notification': self.notification,
            'smWalletBehaviour': self.smWalletBehaviour
        }

    def getActiveExecutions(self) -> List[Tuple[ExecutionState, BaseStrategyConfig]]:
        """
        Get all active executions with their strategy configurations.
        
        This method delegates to the analyticsHandler to retrieve active executions.
        
        Returns:
            List[Tuple[ExecutionState, BaseStrategyConfig]]: List of active executions with their configs
        """
        try:
            return self.analytics.getActiveExecutionsWithConfig()
        except Exception as e:
            logger.error(f"Failed to get active executions: {str(e)}")
            return []

    def __getattr__(self, name: str) -> Any:
        """
        Magic method to delegate method calls to appropriate handlers.
        
        How it works:
        1. When a method is called on SQLitePortfolioDB
        2. If method not found directly, this function is called
        3. Searches for method in all handlers
        4. Returns the method if found
        
        Example:
        db.insert_summary() -> Actually calls portfolio.insert_summary()
        
        Args:
            name: Name of the method being called
            
        Returns:
            Method from appropriate handler
            
        Raises:
            AttributeError: If method not found in any handler
        """
        for handler in [
            self.token,
            self.portfolio, 
            self.walletsInvested, 
            self.job, 
            self.smartMoneyWallets, 
            self.smWalletTopPNLToken,
            self.smartMoneyPerformanceReport,
            self.attention,
            self.volume,
            self.pumpfun,
            self.analytics,
            self.smWalletBehaviour
        ]:
            if hasattr(handler, name):
                return getattr(handler, name)
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def close(self):
        """
        Properly close all database connections.
        
        What it does:
        1. Closes the shared connection manager
        2. Ensures all database resources are released
        
        When to use:
        - When shutting down the application
        - When cleaning up resources
        - In context managers
        """
        self.conn_manager.close()

    def execute_query(self, query: str, params=None):
        """
        Execute a raw SQL query and return the results.
        
        Args:
            query: SQL query to execute
            params: Optional parameters for the query
            
        Returns:
            List of dictionaries containing the query results
            
        Raises:
            Exception: If there's an error executing the query
        """
        try:
            with self.conn_manager.get_connection() as conn:
                # Set row_factory to return dictionaries
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                    
                # Convert rows to dictionaries
                results = [dict(row) for row in cursor.fetchall()]
                return results
                
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            logger.error(f"Query: {query}")
            raise

    @property
    def transaction(self):
        """
        Property to access the transaction context manager.
        
        How to use:
        with db.transaction() as cursor:
            # perform multiple operations in single transaction
            
        Why needed:
        - Ensures atomic operations
        - Manages transaction lifecycle
        - Provides rollback on errors
        
        Returns:
            Context manager for database transactions
        """
        return self.conn_manager.transaction

    @property
    def table_lock(self):
        """
        Property to access table locking mechanism.
        
        How to use:
        with db.table_lock('table_name'):
            # perform thread-safe operations
            
        Why needed:
        - Ensures thread-safe operations
        - Prevents race conditions
        - Manages concurrent access
        
        Returns:
            Context manager for table locking
        """
        return self.conn_manager.table_lock

    def __enter__(self):
        """
        Context manager entry point.
        
        How to use:
        with SQLitePortfolioDB() as db:
            # use database
            
        Why needed:
        - Ensures proper resource management
        - Automatically handles connection lifecycle
        
        Returns:
            SQLitePortfolioDB instance
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit point.
        
        What it does:
        1. Closes database connection
        2. Handles any cleanup needed
        
        When called:
        - When exiting 'with' block
        - Even if an error occurred
        """
        self.close()

    def get_handler(self, handler_type: str) -> Optional[Any]:
        """
        Get specific handler instance by type.
        
        How to use:
        portfolio_handler = db.get_handler('portfolio')
        
        Why needed:
        - Provides direct access to handlers
        - Useful for specialized operations
        - Enables handler-specific functionality
        
        Args:
            handler_type: Type of handler ('portfolio', 'token_analysis', 'jobs')
            
        Returns:
            Handler instance or None if not found
        """
        handlers = {
            'token': self.token,
            'portfolio': self.portfolio,
            'port_summary_report': self.portfolio,
            'token_analysis': self.walletsInvested,
            'jobs': self.job,
            'wallet_behaviour': self.smartMoneyWallets,
            'top_pnl_token': self.smWalletTopPNLToken,
            'attention': self.attention,
            'volume': self.volume,
            'pumpfun': self.pumpfun,
            'analytics': self.analytics,
            'smWalletBehaviour': self.smWalletBehaviour
        }
        return handlers.get(handler_type)