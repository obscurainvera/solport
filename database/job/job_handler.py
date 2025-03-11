from database.operations.base_handler import BaseSQLiteHandler
from typing import List, Dict, Optional
from datetime import datetime
import sqlite3
from logs.logger import get_logger

logger = get_logger(__name__)

class JobHandler(BaseSQLiteHandler):
    def __init__(self, conn_manager):
        super().__init__(conn_manager)  # Properly initialize base class
        self._createTables()

    def _createTables(self):
        with self.conn_manager.transaction() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS joblocks (
                    jobid TEXT PRIMARY KEY,
                    lockedat TIMESTAMP NOT NULL,
                    timeout INTEGER NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS jobexecutions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jobid TEXT NOT NULL,
                    starttime TIMESTAMP NOT NULL,
                    endtime TIMESTAMP,
                    status TEXT NOT NULL,
                    errormessage TEXT,
                    createdat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

    def acquireLock(self, jobId: str, timeout: int = 3600) -> bool:
        try:
            with self.connManager.transaction() as cursor:
                # Clean up expired locks first
                cursor.execute("""
                    DELETE FROM joblocks 
                    WHERE datetime(lockedat, '+' || timeout || ' seconds') < datetime('now')
                """)
                
                # Try to acquire lock
                cursor.execute("""
                    INSERT INTO joblocks (jobid, lockedat, timeout)
                    VALUES (?, datetime('now'), ?)
                """, (jobId, timeout))
                return True
        except sqlite3.IntegrityError:
            # Lock already exists
            return False
        except Exception as e:
            logger.error(f"Failed to acquire lock for job {jobId}: {str(e)}")
            return False

    def releaseLock(self, jobId: str) -> bool:
        try:
            with self.connManager.transaction() as cursor:
                cursor.execute("DELETE FROM joblocks WHERE jobid = ?", (jobId,))
                return True
        except Exception as e:
            logger.error(f"Failed to release lock for job {jobId}: {str(e)}")
            return False

    def startJobExecution(self, jobId: str) -> int:
        try:
            with self.connManager.transaction() as cursor:
                cursor.execute("""
                    INSERT INTO jobexecutions 
                    (jobid, starttime, status)
                    VALUES (?, datetime('now'), 'RUNNING')
                """, (jobId,))
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to start job execution for {jobId}: {str(e)}")
            raise

    def completeJobExecution(self, executionId: int, status: str, errorMessage: Optional[str] = None) -> bool:
        try:
            with self.connManager.transaction() as cursor:
                cursor.execute("""
                    UPDATE jobexecutions 
                    SET status = ?,
                        errormessage = ?,
                        endtime = datetime('now')
                    WHERE id = ?
                """, (status, errorMessage, executionId))
                return True
        except Exception as e:
            logger.error(f"Failed to complete job execution {executionId}: {str(e)}")
            return False

    def getJobStatus(self, jobId: str) -> Dict:
        try:
            with self.connManager.transaction() as cursor:
                cursor.execute("""
                    SELECT * FROM jobexecutions
                    WHERE jobid = ?
                    ORDER BY starttime DESC
                    LIMIT 1
                """, (jobId,))
                row = cursor.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            logger.error(f"Failed to get job status for {jobId}: {str(e)}")
            return {}

    def getRunningJobs(self) -> List[Dict]:
        try:
            with self.connManager.transaction() as cursor:
                cursor.execute("""
                    SELECT * FROM jobexecutions
                    WHERE status = 'RUNNING'
                    AND datetime(starttime, '+1 hour') > datetime('now')
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get running jobs: {str(e)}")
            return []

    def cleanupOldExecutions(self, days: int = 30) -> bool:
        try:
            with self.connManager.transaction() as cursor:
                cursor.execute("""
                    DELETE FROM jobexecutions
                    WHERE datetime(createdat, '+' || ? || ' days') < datetime('now')
                """, (days,))
                return True
        except Exception as e:
            logger.error(f"Failed to cleanup old executions: {str(e)}")
            return False

    def getJobHistory(self, jobId: str, limit: int = 100) -> List[Dict]:
        try:
            with self.connManager.transaction() as cursor:
                cursor.execute("""
                    SELECT 
                        id,
                        jobid,
                        starttime,
                        endtime,
                        status,
                        errormessage,
                        createdat
                    FROM jobexecutions
                    WHERE jobid = ?
                    ORDER BY starttime DESC
                    LIMIT ?
                """, (jobId, limit))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get job history for {jobId}: {str(e)}")
            return []

    def getFailedJobs(self, hours: int = 24) -> List[Dict]:
        try:
            with self.connManager.transaction() as cursor:
                cursor.execute("""
                    SELECT * FROM jobexecutions
                    WHERE status = 'FAILED'
                    AND datetime(createdat, '+' || ? || ' hours') > datetime('now')
                    ORDER BY starttime DESC
                """, (hours,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get failed jobs: {str(e)}")
            return [] 