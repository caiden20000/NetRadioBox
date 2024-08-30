"""Provides a definition for each operating mode of the Radio interface"""
from enum import Enum

class Mode(Enum):
    """Mode Enum used for representing each mode."""
    STATION = 1
    TIME = 2
    ALARM = 3
    MODE = 4
