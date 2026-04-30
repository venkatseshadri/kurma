"""
🐢 Kurma - MCX Intraday Trading Bot
Evening session momentum trading system (5:00 PM - 11:20 PM IST)

Author: Kubera 🦞
Date: Apr 30, 2026
"""

__version__ = "1.0"
__author__ = "Kubera"
__description__ = "MCX Intraday Trading Bot - Margin-efficient commodity futures scalping"

from kurma_main import KurmaOrchestrator, KurmaConfig
from kurma_selector import KurmaSelector
from kurma_momentum import KurmaMomentum, PartialTPTrailingStopLogic
from kurma_eod_analyzer import KurmaEODAnalyzer

__all__ = [
    'KurmaOrchestrator',
    'KurmaConfig',
    'KurmaSelector',
    'KurmaMomentum',
    'PartialTPTrailingStopLogic',
    'KurmaEODAnalyzer'
]
