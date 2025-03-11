# database/operations/smwallet_behaviour_handler.py
from database.operations.base_handler import BaseSQLiteHandler
from typing import List
from datetime import datetime
from logs.logger import get_logger
import pandas as pd
from database.operations.schema import SMWalletBehaviour

logger = get_logger(__name__)

class SMWalletBehaviourHandler(BaseSQLiteHandler):
    def __init__(self, connManager):
        super().__init__(connManager)
        self.createSMWalletBehaviourAnalysisTables()

    def createSMWalletBehaviourAnalysisTables(self):
        """Create the smwallet_behaviour_analysis table if it doesn't exist"""
        with self.connManager.transaction() as cursor:
            cursor.execute('''
                create table if not exists smwalletbehaviour (
                    walletaddress text primary key,
                    totalinvestment decimal,
                    numtokens integer,
                    avginvestmentpertoken decimal,
                    highconvictionnumtokens integer,
                    highconvictionavginvestment decimal,
                    mediumconvictionnumtokens integer,
                    mediumconvictionavginvestment decimal,
                    lowconvictionnumtokens integer,
                    lowconvictionavginvestment decimal,
                    analysistime timestamp
                )
            ''')
            logger.info("SMWallet behaviour analysis table ensured")

    def getWalletInvestmentData(self) -> pd.DataFrame:
        """Fetch investment data from smwallettoppnltoken"""
        try:
            query = """
                select walletaddress, tokenid, amountinvested, unprocessedpnl, unprocessedroi
                from smwallettoppnltoken
            """
            df = pd.read_sql_query(query, self.connManager.get_connection())
            logger.info(f"Fetched {len(df)} records from smwallettoppnltoken")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch wallet investment data: {str(e)}")
            raise

    def storeSMWalletBehaviourAnalysis(self, smbehaviouranalysis: List[SMWalletBehaviour]):
        """Store analysis results in the database"""
        try:
            with self.connManager.transaction() as cursor:
                for smbehaviour in smbehaviouranalysis:
                    cursor.execute('''
                        insert or replace into smwalletbehaviour (
                            walletaddress, totalinvestment, numtokens, avginvestmentpertoken,
                            highconvictionnumtokens, highconvictionavginvestment,
                            mediumconvictionnumtokens, mediumconvictionavginvestment,
                            lowconvictionnumtokens, lowconvictionavginvestment, analysistime
                        ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        smbehaviour.walletaddress, smbehaviour.totalinvestment, smbehaviour.numtokens,
                        smbehaviour.avginvestmentpertoken, smbehaviour.highconvictionnumtokens,
                        smbehaviour.highconvictionavginvestment, smbehaviour.mediumconvictionnumtokens,
                        smbehaviour.mediumconvictionavginvestment, smbehaviour.lowconvictionnumtokens,
                        smbehaviour.lowconvictionavginvestment, smbehaviour.analysistime
                    ))
            logger.info(f"Stored analysis for {len(smbehaviouranalysis)} wallets")
        except Exception as e:
            logger.error(f"Failed to store analysis results: {str(e)}")
            raise