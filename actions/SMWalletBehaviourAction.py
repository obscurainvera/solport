# actions/smwallet_behaviour_action.py
from database.operations.sqlite_handler import SQLitePortfolioDB
from database.smwalletsbehaviour.SMWalletBehaviourHandler import SMWalletBehaviourHandler
from database.operations.schema import SMWalletBehaviour
from logs.logger import get_logger
from datetime import datetime
import pandas as pd
from typing import List

logger = get_logger(__name__)

class SMWalletBehaviourAction:
    """Handles SM wallet investment behavior analysis workflow"""
    
    def __init__(self, db: SQLitePortfolioDB):
        self.db = db
        self.handler = SMWalletBehaviourHandler(db.connManager)

    def analyzeSMWalletBehaviour(self) -> bool:
        """Execute the wallet behavior analysis"""
        try:
            logger.info("Starting SM wallet behaviour analysis")
            df = self.handler.getWalletInvestmentData()
            if df.empty:
                logger.warning("No data available for analysis")
                return False

            # Estimate investments
            df['investment'] = df.apply(self.estimateInvestement, axis=1)
            df = df[df['investment'] > 0]  # Filter out invalid investments
            if df.empty:
                logger.warning("No valid investment data after estimation")
                return False

            # Compute metrics and build analysis objects
            smbehaviouranalysisList = self.computeMetrics(df)
            if not smbehaviouranalysisList:
                logger.warning("No analysis results generated")
                return False

            # Store results
            self.handler.storeSMWalletBehaviourAnalysis(smbehaviouranalysisList)
            logger.info("SM wallet behaviour analysis completed successfully")
            return True

        except Exception as e:
            logger.error(f"SM wallet behaviour analysis failed: {str(e)}")
            return False

    def estimateInvestement(self, row) -> float:
        """Estimate investment when amountInvested is unavailable"""
        if pd.notnull(row['amountinvested']) and row['amountinvested'] > 0:
            return row['amountinvested']
        elif (pd.notnull(row['unprocessedpnl']) and pd.notnull(row['unprocessedroi']) and
              row['unprocessedroi'] != 0):
            # Estimate cost of sold portion: unprocessedpnl / (unprocessedroi / 100)
            costSold = (row['unprocessedpnl'] * 100) / row['unprocessedroi']
            return costSold if costSold > 0 else 0
        return 0

    def computeMetrics(self, df: pd.DataFrame) -> List[SMWalletBehaviour]:
        """Compute investment metrics for all wallets"""
        SMWalletBehaviourAnalysisList = []
        for walletAddress, group in df.groupby('walletaddress'):
            totalInvestment = group['investment'].sum()
            numTokens = len(group)
            if numTokens == 0 or totalInvestment == 0:
                SMWalletBehaviourAnalysisList.append(SMWalletBehaviour(
                    walletaddress=walletAddress,
                    totalinvestment=0,
                    numtokens=0,
                    avginvestmentpertoken=0,
                    highconvictionnumtokens=0,
                    highconvictionavginvestment=0,
                    mediumconvictionnumtokens=0,
                    mediumconvictionavginvestment=0,
                    lowconvictionnumtokens=0,
                    lowconvictionavginvestment=0,
                    analysistime=datetime.now()
                ))
                continue

            avgInvestmentPerToken = totalInvestment / numTokens
            weights = group['investment'] / totalInvestment

            # Define conviction categories
            highConv = weights >= 0.1
            medConv = (weights >= 0.02) & (weights < 0.1)
            lowConv = weights < 0.02

            SMWalletBehaviourAnalysisList.append(SMWalletBehaviour(
                walletaddress=walletAddress,
                totalinvestment=totalInvestment,
                numtokens=numTokens,
                avginvestmentpertoken=avgInvestmentPerToken,
                highconvictionnumtokens=highConv.sum(),
                highconvictionavginvestment=group[highConv]['investment'].mean() or 0,
                mediumconvictionnumtokens=medConv.sum(),
                mediumconvictionavginvestment=group[medConv]['investment'].mean() or 0,
                lowconvictionnumtokens=lowConv.sum(),
                lowconvictionavginvestment=group[lowConv]['investment'].mean() or 0,
                analysistime=datetime.now()
            ))
        return SMWalletBehaviourAnalysisList