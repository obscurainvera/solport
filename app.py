from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import time
import signal
import threading
import os
import json
from decimal import Decimal
from sqlalchemy import create_engine, text
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from logs.logger import get_logger
from api.walletsinvested.WalletsInvestedAPI import wallets_invested_bp, CustomJSONEncoder
from api.walletsinvested.WalletsInvestedInvestmentDetailsAPI import wallets_invested_investement_details_bp
from api.portsummary.PortfolioAPI import portfolio_bp
from api.operations.HealthAPI import health_bp
from api.operations.DashboardAPI import dashboard_bp
from api.operations.AnalyticsAPI import analytics_bp
from api.smartmoney.SmartMoneyWalletsAPI import smart_money_wallets_bp
from api.smartmoney.SMWalletTopPNLTokenAPI import smwallet_top_pnl_token_bp
from api.smartmoney.SMWalletTopPNLTokenInvestmentAPI import smwallet_top_pnl_token_investment_bp
from api.attention.AttentionAPI import attention_bp
from api.volume.VolumebotAPI import volumebot_bp
from api.pumpfun.PumpfunAPI import pumpfun_bp  
from api.operations.SchedulerAPI import scheduler_bp
from api.portsummary.PortfolioTaggerAPI import portfolio_tagger_bp
from api.analyticsframework.CreateStrategyAPI import strategy_bp
from api.analyticsframework.PushTokenFrameworkAPI import push_token_bp
from framework.analyticsframework.enums.SourceTypeEnum import SourceType
from api.operations.StrategyAPI import strategy_page_bp
from api.analyticsframework.ExecutionMonitorAPI import execution_monitor_bp
from api.smartmoneywalletsbehaviour.SmartMoneyWalletsBehaviourAPI import smartMoneyWalletBehaviourBp
from api.operations.ReportsAPI import reports_page_bp
from api.portsummary.PortSummaryReportAPI import port_summary_report_bp
from api.smartmoney.SmartMoneyWalletsReportAPI import smartMoneyWalletsReportBp
from api.smartmoney.SmartMoneyPerformanceReportAPI import smartMoneyPerformanceReportBp
from api.strategyreport.StrategyReportAPI import strategy_report_bp
from api.strategyreport.StrategyPerformanceAPI import strategyperformance_bp
from api.smwalletsbehaviour.SMWalletBehaviourReportAPI import smwalletBehaviourReportBp
from api.smwalletsbehaviour.SMWalletInvestmentRangeReportAPI import smwallet_investment_range_report_bp
from api.portfolioallocation.PortfolioAllocationAPI import portfolio_allocation_bp
from api.attention.AttentionReportAPI import attention_report_bp
from api.dexscrenner.DexScrennerAPI import dexscrenner_bp
from api.smartmoney.SmartMoneyMovementsAPI import smart_money_movements_bp
from api.smartmoney.SmartMoneyMovementsSchedulerAPI import smart_money_movements_scheduler_bp
from api.smartmoneymovements.SmartMoneyMovementsReportAPI import smartMoneyMovementsReportBp
from api.superport.SuperPortReportAPI import superport_report_bp
from api.toptraders.TopTradersAPI import top_traders_bp
from api.smartmoneypnl.SmartMoneyPNLReportAPI import smart_money_pnl_report_bp

logger = get_logger(__name__)

from scheduler.JobRunner import JobRunner
from database.operations.sqlite_handler import SQLitePortfolioDB

logger = get_logger(__name__)

def initialize_job_storage():
    """Initialize job storage and required tables"""
    try:
        # We need to create a database engine to interact with the 'jobs.db' file, 
        # which stores information about scheduled jobs. This engine is used to 
        # create the necessary tables for job storage.
        engine = create_engine('sqlite:///jobs.db')
        
        # Create monitoring tables
        with engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS job_locks (
                    job_id TEXT PRIMARY KEY,
                    locked_at TIMESTAMP NOT NULL,
                    timeout INTEGER NOT NULL
                )
            """))
            
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS job_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    end_time TIMESTAMP,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
        logger.info("Job storage initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize job storage: {e}")
        raise

class PortfolioApp:
    """
    Main application class that manages the Flask web server and background jobs.
    Handles graceful startup/shutdown and provides health monitoring endpoints.
    """
    
    def __init__(self):
        """
        Initialize core components:
        - Flask web server
        - Background job scheduler
        - Shutdown flag for graceful termination
        """
        logger.info("Initializing Portfolio App...")
        self.app = Flask(__name__, 
                         static_folder='frontend/solport/build/static',
                         template_folder='frontend/solport/build')
        
        # Configure CORS
        CORS(self.app, resources={r"/api/*": {"origins": "*"}})
        
        # Configure JSON encoder to handle Decimal objects
        self.app.json_encoder = CustomJSONEncoder
        
        try:
            initialize_job_storage()
            self.job_runner = JobRunner()
            self.is_shutting_down = threading.Event()
            
            # Register API blueprints
            self.app.register_blueprint(wallets_invested_bp)
            self.app.register_blueprint(wallets_invested_investement_details_bp)
            self.app.register_blueprint(portfolio_bp)
            self.app.register_blueprint(health_bp)
            self.app.register_blueprint(dashboard_bp)
            self.app.register_blueprint(analytics_bp)
            self.app.register_blueprint(smart_money_wallets_bp)
            self.app.register_blueprint(smwallet_top_pnl_token_bp)
            self.app.register_blueprint(smwallet_top_pnl_token_investment_bp)
            self.app.register_blueprint(smartMoneyWalletsReportBp)
            self.app.register_blueprint(attention_bp)
            self.app.register_blueprint(volumebot_bp)
            self.app.register_blueprint(pumpfun_bp)
            self.app.register_blueprint(scheduler_bp)
            self.app.register_blueprint(portfolio_tagger_bp)
            self.app.register_blueprint(strategy_bp)
            self.app.register_blueprint(push_token_bp)
            self.app.register_blueprint(strategy_page_bp)
            self.app.register_blueprint(execution_monitor_bp)
            self.app.register_blueprint(smartMoneyWalletBehaviourBp)
            self.app.register_blueprint(reports_page_bp)
            self.app.register_blueprint(port_summary_report_bp)
            self.app.register_blueprint(smartMoneyPerformanceReportBp)
            self.app.register_blueprint(strategy_report_bp)
            self.app.register_blueprint(smwallet_investment_range_report_bp)
            self.app.register_blueprint(smwalletBehaviourReportBp)
            self.app.register_blueprint(strategyperformance_bp)
            self.app.register_blueprint(portfolio_allocation_bp)
            self.app.register_blueprint(attention_report_bp)
            self.app.register_blueprint(dexscrenner_bp)
            self.app.register_blueprint(smart_money_movements_bp)
            self.app.register_blueprint(smart_money_movements_scheduler_bp)
            self.app.register_blueprint(smartMoneyMovementsReportBp)
            self.app.register_blueprint(superport_report_bp)
            self.app.register_blueprint(top_traders_bp)
            self.app.register_blueprint(smart_money_pnl_report_bp)
            
            logger.info("Portfolio app initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize PortfolioApp: {e}")
            raise
        
    def _setup_signal_handlers(self):
        """
        Configure system signal handlers (Ctrl+C, kill, etc.)
        Ensures graceful shutdown when the application is terminated
        """
        def handle_signal(signum, frame):
            if not self.is_shutting_down.is_set():
                logger.info(f"\n🛑 Received shutdown signal {signum}")
                self.shutdown()
                os._exit(0)  # Force exit to avoid threading issues

        signal.signal(signal.SIGINT, handle_signal)   # Handle Ctrl+C
        signal.signal(signal.SIGTERM, handle_signal)  # Handle kill command
        logger.info("✅ Signal handlers configured")

    def shutdown(self):
        """
        Graceful shutdown sequence:
        1. Set shutdown flag to prevent new operations
        2. Stop background job scheduler
        3. Close database connections
        """
        if not self.is_shutting_down.is_set():
            self.is_shutting_down.set()
            
            logger.info("Shutting down job runner...")
            self.job_runner.shutdown()
            logger.info("✅ Job runner stopped")

            try:
                logger.info("Closing database connections...")
                SQLitePortfolioDB().close()
                logger.info("✅ Database connections closed")
            except Exception as e:
                logger.error(f"Error closing database: {e}")

    def run(self, host='0.0.0.0', port=8080):
        """
        Start the application:
        1. Setup signal handlers for graceful shutdown
        2. Start background jobs
        3. Launch Flask web server
        
        Args:
            host: Network interface to bind to
            port: Port number to listen on
        """
        try:
            self._setup_signal_handlers()
            self.job_runner.start()
            logger.info("✅ Background jobs started")
            
            logger.info("\n🚀 Starting Portfolio Monitoring System")
            logger.info(f"🔗 API available at http://{host}:{port}")
            
            self.app.run(
                host=host,
                port=port,
                debug=False,
                use_reloader=False,  # Prevent duplicate processes
                threaded=True        # Enable concurrent request handling
            )
            
        except Exception as e:
            logger.error(f"🔥 Critical startup error: {e}")
            self.shutdown()
            raise

def create_app():
    """Factory function for creating application instance"""
    return PortfolioApp()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app = create_app()
    app.run(port=port)
