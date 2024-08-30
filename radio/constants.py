"""Constants for the radio app."""

import time

# Gets the current time in ms
# MS is the default representation of all integer times in this program.
def time_now() -> int:
    """Current time in ms"""
    return time.time_ns() // 1_000_000