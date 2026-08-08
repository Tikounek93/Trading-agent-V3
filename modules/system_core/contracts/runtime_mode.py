"""Supported system operation modes."""

from enum import Enum


class RuntimeMode(str, Enum):
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"
