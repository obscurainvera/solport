from logs.logger import get_logger
from apscheduler.schedulers.background import BackgroundScheduler
from scheduler.PortfolioScheduler import PortfolioScheduler
from scheduler.WalletsInvestedScheduler import WalletsInvestedScheduler
from scheduler.VolumebotScheduler import VolumeBotScheduler
from scheduler.PumpfunScheduler import PumpFunScheduler
from actions.WalletsInvestedInvestmentDetailsAction import  WalletsInvestedInvestmentDetailsAction
from database.operations.sqlite_handler import SQLitePortfolioDB
from apscheduler.schedulers.base import SchedulerNotRunningError, SchedulerAlreadyRunningError
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED
from config.SchedulerConfig import SCHEDULER_CONFIG
from scheduler.AttentionScheduler import AttentionScheduler
from scheduler.DeactivateLostSMBalanceTokens import DeactiveLostSMBalanceTokens
from scheduler.ExecutionMonitorScheduler import ExecutionMonitorScheduler
import time
import requests
import sqlite3

logger = get_logger(__name__)

def handleWalletsInvestedInPortSummaryTokens(db_path: str = 'portfolio.db'):
    """Standalone function to execute token analysis updates."""
    logger.info("Starting token analysis execution")
    scheduler = None
    try:
        scheduler = WalletsInvestedScheduler(db_path)
        scheduler.handleWalletsInvestedInPortSummaryTokens()
        logger.info("Token analysis completed successfully")
    except Exception as e:
        logger.error(f"Token analysis job failed: {e}")
        raise

def handlePortfolioSummary(db_path: str = 'portfolio.db'):
    """
    Standalone function to execute portfolio updates.
    Creates fresh instances for each execution to avoid serialization issues.
    """
    logger.info("Starting portfolio update execution")
    scheduler = None
    try:
        scheduler = PortfolioScheduler(db_path)
        scheduler.handlePortfolioSummaryUpdate()
        logger.info("Portfolio update completed successfully")
        
    except (requests.exceptions.RequestException, 
            sqlite3.OperationalError,
            TimeoutError,
            ConnectionError) as e:
        logger.warning(f"Encountered retryable error: {e}")
        time.sleep(SCHEDULER_CONFIG['job_defaults'].get('retry_delay', 300))
        
        try:
            if scheduler:
                scheduler.handlePortfolioSummaryUpdate()
                logger.info("Portfolio update completed successfully on retry")
        except Exception as retry_error:
            logger.error(f"Job failed after retry: {retry_error}")
            raise
            
    except Exception as e:
        logger.error(f"Job failed with non-retryable error: {e}")
        raise

def handleTokenDeactivation(db_path: str = 'portfolio.db'):
    """Standalone function to execute token deactivation."""
    logger.info("Starting token deactivation execution")
    try:
        scheduler = DeactiveLostSMBalanceTokens(db_path)
        scheduler.handleTokenDeactivation()
        logger.info("Token deactivation completed successfully")
    except Exception as e:
        logger.error(f"Token deactivation job failed: {e}")
        raise

def handleVolumeBotAnalysis(db_path: str = 'portfolio.db'):
    """Standalone function to execute volume bot updates."""
    logger.info("Starting volume bot execution")
    try:
        scheduler = VolumeBotScheduler(db_path)
        scheduler.handleVolumeAnalysisFromJob()
        logger.info("Volume bot completed successfully")
    except Exception as e:
        logger.error(f"Volume bot job failed: {e}")
        raise

def handlePumpFunAnalysis(db_path: str = 'portfolio.db'):
    """Standalone function to execute pump fun updates."""
    logger.info("Starting pump fun execution")
    try:
        scheduler = PumpFunScheduler(db_path)
        scheduler.handlePumpFunAnalysisFromJob()
        logger.info("Pump fun completed successfully")
    except Exception as e:
        logger.error(f"Pump fun job failed: {e}")
        raise

def handleExecutionMonitoring(db_path: str = 'portfolio.db'):
    """Standalone function to execute active strategy monitoring."""
    logger.info("Starting execution monitoring cycle")
    try:
        scheduler = ExecutionMonitorScheduler(db_path)
        scheduler.handleActiveExecutionsMonitoring()
        logger.info("Execution monitoring completed successfully")
    except Exception as e:
        logger.error(f"Execution monitoring job failed: {e}")
        raise

class JobRunner:
    """
    Manages all scheduled jobs in the application with persistent storage.
    Handles multiple jobs accessing same database tables with proper locking.
    """
    
    def __init__(self, db_path: str = 'portfolio.db'):
        """
        Initialize job runner with configuration
        
        Args:
            db_path: Path to portfolio database
        """
        self.db_path = db_path
        self.portfolio_scheduler = PortfolioScheduler(db_path)
        self.scheduler = BackgroundScheduler(**SCHEDULER_CONFIG)
        
        # Add event listener for job monitoring
        self.scheduler.add_listener(
            self._job_listener,
            EVENT_JOB_ERROR | EVENT_JOB_EXECUTED
        )
        logger.info("JobRunner initialized")

    def addPortfolioSummaryJobs(self):
        """
        Add portfolio related jobs with retry mechanism
        """
        self.scheduler.add_job(
            func=handlePortfolioSummary,
            args=[self.db_path],
            trigger='cron',
            hour='*/6',     # Every 4 hours (0, 4, 8, 12, 16, 20)
            minute='0',
            id='portfolio_summary_analysis',
            name='Portfolio Summary Analysis',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        
    def addWalletsInvestedInATokenJobs(self):
        """Add token analysis job - runs every hour"""
        self.scheduler.add_job(
            func=handleWalletsInvestedInPortSummaryTokens,
            args=[self.db_path],
            trigger='cron',
            hour='*/6',     # Every 4 hours (0, 4, 8, 12, 16, 20)
            minute='0',
            id='wallets_invested_in_a_token',
            name='Wallets Invested in a Token',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )

    def addAttentionAnalysisJobs(self):
        """Add attention analysis job - runs every hour"""
        attention_scheduler = AttentionScheduler()
        self.scheduler.add_job(
            attention_scheduler.handleAttentionData,
            'cron',
            hour='*',
            minute='0',
            id='attention_analysis',
            name='Token Attention Analysis',
            max_instances=1,
            coalesce=True,
            misfire_grace_time=900,
            replace_existing=True  # Added this parameter
        )
        logger.info("Scheduled attention analysis job (hourly at :00)")

    def addTokenDeactivationJob(self):
        """Add token deactivation job - runs daily"""
        self.scheduler.add_job(
            func=handleTokenDeactivation,
            args=[self.db_path],
            trigger='cron',
            hour='0',  # Run at midnight
            minute='0',
            id='daily_token_deactivation',
            name='Daily Token Deactivation',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        logger.info("Scheduled token deactivation job (daily at midnight)")

    def addVolumeBotJobs(self):
        """Add volume bot job - runs every 30 seconds using cron"""
        self.scheduler.add_job(
            func=handleVolumeBotAnalysis,
            args=[self.db_path],
            trigger='cron',
            second='*/30',  # Run every 30 seconds
            id='volume_bot_analysis',
            name='Volume Bot Analysis',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        logger.info("Scheduled volume bot job (every 30 seconds)")

    def addPumpFunJobs(self):
        """Add pump fun job - runs every 30 seconds using cron"""
        self.scheduler.add_job(
            func=handlePumpFunAnalysis,
            args=[self.db_path],
            trigger='cron',
            second='*/30',  # Run every 30 seconds
            id='pump_fun_analysis',
            name='Pump Fun Analysis',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        logger.info("Scheduled pump fun job (every 30 seconds)")

    def addExecutionMonitoringJobs(self):
        """Add execution monitoring job - runs every minute"""
        self.scheduler.add_job(
            func=handleExecutionMonitoring,
            args=[self.db_path],
            trigger='cron',
            minute='*',  # Run every minute
            id='execution_monitoring',
            name='Strategy Execution Monitoring',
            replace_existing=True,
            max_instances=1,
            coalesce=True
        )
        logger.info("Scheduled execution monitoring job (every minute)")

    def setup_jobs(self):
        try:
            existing_jobs = self.scheduler.get_jobs()
            job_ids = [job.id for job in existing_jobs]
            
            # Check and add each job type separately
            if 'portfolio_summary_analysis' not in job_ids:
                self.addPortfolioSummaryJobs()
            
            if 'wallets_invested_in_a_token' not in job_ids:
                self.addWalletsInvestedInATokenJobs()
            
            if 'attention_analysis' not in job_ids:
                self.addAttentionAnalysisJobs()

            if 'daily_token_deactivation' not in job_ids:
                self.addTokenDeactivationJob()

            if 'volume_bot_analysis' not in job_ids:
                self.addVolumeBotJobs()

            if 'pump_fun_analysis' not in job_ids:
                self.addPumpFunJobs()
            
            if 'execution_monitoring' not in job_ids:
                self.addExecutionMonitoringJobs()
            
            logger.info("All jobs configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup jobs: {e}")
            raise

    def _job_listener(self, event):
        """Handle job execution events"""
        if event.exception:
            logger.error(f"Job {event.job_id} raised an exception: {event.exception}")
            self._record_job_execution(event.job_id, 'error', str(event.exception))
        else:
            logger.info(f"Job {event.job_id} executed successfully")
            self._record_job_execution(event.job_id, 'success')
            
    def _record_job_execution(self, job_id, status, error_message=None, start_time=None):
        """Record job execution in the database using JobHandler"""
        try:
            from database.operations.sqlite_handler import SQLitePortfolioDB
            
            # Use the JobHandler to record the execution
            with SQLitePortfolioDB() as db:
                if hasattr(db, 'job') and db.job is not None:
                    job_handler = db.job
                    
                    if status == 'success':
                        # For successful executions, we need to start and complete in one go
                        execution_id = job_handler.startJobExecution(job_id)
                        job_handler.completeJobExecution(execution_id, 'COMPLETED')
                        logger.info(f"Recorded successful execution for job {job_id}")
                    elif status == 'error':
                        # For failed executions, record with error message
                        execution_id = job_handler.startJobExecution(job_id)
                        job_handler.completeJobExecution(execution_id, 'FAILED', error_message)
                        logger.info(f"Recorded failed execution for job {job_id}")
                else:
                    logger.error("JobHandler not available in database connection")
        except Exception as e:
            logger.error(f"Error recording job execution: {e}")

    def start(self):
        try:
            if not self.scheduler.running:
                self.setup_jobs()
                self.scheduler.start()
                logger.info("Scheduler started successfully")
            else:
                logger.warning("Scheduler is already running")
                
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise

    def shutdown(self):
        try:
            if self.scheduler.running:
                logger.info("Shutting down scheduler...")
                self.scheduler.shutdown(wait=False)
                logger.info("Scheduler shutdown complete")
            else:
                logger.warning("Scheduler is already stopped")
                
        except Exception as e:
            logger.error(f"Error during scheduler shutdown: {e}")
            raise

    def update_job_schedule(self, job_id: str, **schedule_args):
        """
        Update the schedule of an existing job
        
        Args:
            job_id: ID of the job to update
            schedule_args: New schedule parameters (e.g., second='*/45', hour='*/2', etc.)
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.reschedule(trigger='cron', **schedule_args)
                logger.info(f"Successfully updated schedule for job {job_id}")
            else:
                logger.warning(f"Job {job_id} not found")
            
        except Exception as e:
            logger.error(f"Failed to update job schedule: {e}")
            raise

    def modify_job_timing(self, job_id: str, timing_type: str, value: str):
        """
        Modify specific timing for a job
        
        Args:
            job_id: ID of the job to modify
            timing_type: Type of timing to modify (second, minute, hour, etc.)
            value: New value for the timing
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                current_trigger = job.trigger
                trigger_args = {}
                
                # Preserve existing trigger arguments
                for field in current_trigger.fields:
                    if field.name != timing_type:
                        trigger_args[field.name] = str(field)
                
                # Add new timing value
                trigger_args[timing_type] = value
                
                # Reschedule job with updated timing
                job.reschedule(trigger='cron', **trigger_args)
                logger.info(f"Successfully modified {timing_type} to {value} for job {job_id}")
            else:
                logger.warning(f"Job {job_id} not found")
            
        except Exception as e:
            logger.error(f"Failed to modify job timing: {e}")
            raise

    def run_job(self, job_id: str, external_scheduler=None):
        """
        Run a job immediately
        
        Args:
            job_id: ID of the job to run
            external_scheduler: Optional external scheduler instance to use
        """
        try:
            # Use the provided external scheduler if available, otherwise use self.scheduler
            scheduler_to_use = external_scheduler if external_scheduler else self.scheduler
            
            job = scheduler_to_use.get_job(job_id)
            if job:
                # Get the job function
                job_func = job.func
                
                # Record start of execution
                start_time = time.time()
                logger.info(f"Starting execution of job {job_id}")
                
                try:
                    # Run the job function immediately
                    job_func()
                    
                    # Record successful execution
                    self._record_job_execution(job_id, 'success', start_time=start_time)
                    logger.info(f"Successfully ran job {job_id}")
                    return True
                except Exception as e:
                    # Record failed execution
                    self._record_job_execution(job_id, 'error', error_message=str(e), start_time=start_time)
                    logger.error(f"Error running job {job_id}: {e}")
                    raise
            else:
                logger.warning(f"Job {job_id} not found in scheduler")
                return False
                
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
            raise

