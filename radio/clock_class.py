"""
Clock class. Keeps track of user-defined time offset and alarm.
"""

import threading
import time
from datetime import datetime
from typing import Callable


# Since we always have ms since epoch, "setting the time" should be as an offset to that.
# Alarm is stored as minutes from 0000 (midnight) 
MINUTES_IN_DAY = 60 * 24
SECONDS_IN_DAY = 60 * MINUTES_IN_DAY
class Clock:
    def __init__(self):
        # Offset from system time (in seconds)
        self.current_time_offset = 0
        # Alarm time in MINUTES from midnight.
        self.alarm_time = 0
        self.alarm_active = False
        self.alarm_callback = None
        self.alarm_timer = None

    def _seconds_through_day(self) -> int:
        now = datetime.now()
        start_of_day = datetime(year=now.year, month=now.month, day=now.day)
        time_difference = now - start_of_day
        return time_difference.total_seconds()

    def _get_time_from_seconds_through_day(self, total_seconds: int) -> tuple[int, int, int]:
        total_seconds %= SECONDS_IN_DAY
        total_minutes = total_seconds // 60
        total_hours = total_minutes // 60
        seconds = total_seconds % 60
        minutes = total_minutes % 60
        hours = total_hours % 24
        return (hours, minutes, seconds)

    def _get_time_from_minutes_through_day(self, total_minutes: int) -> tuple[int, int, int]:
        return self._get_time_from_seconds_through_day(total_minutes * 60)

    def _get_seconds_until_alarm(self) -> int:
        alarm_seconds = self.alarm_time * 60
        delta_time = alarm_seconds - self._seconds_through_day()
        time_until_alarm = delta_time if delta_time > 0 else delta_time + SECONDS_IN_DAY
        return time_until_alarm

    def set_time_to_system_time(self) -> None:
        self.current_time_offset = 0

    def set_current_time_offset(self, new_time_seconds: int) -> None:
        self.current_time_offset = new_time_seconds % SECONDS_IN_DAY

    def scrub_current_time_offset(self, change_seconds: int) -> None:
        self.set_current_time_offset(self.current_time_offset + change_seconds)

    def set_alarm_time(self, new_time_minutes: int) -> None:
        self.alarm_time = new_time_minutes % MINUTES_IN_DAY

    def scrub_alarm_time(self, change_minutes: int) -> None:
        self.set_alarm_time(self.alarm_time + change_minutes)

    def _init_alarm(self) -> None:
        if self.alarm_timer is not None:
            self.alarm_timer.cancel()
        self.alarm_timer = threading.Timer(self._get_seconds_until_alarm(), self._prealarm)
        self.alarm_timer.start()

    def _prealarm(self) -> None:
        print(">>>>> Alarm!")
        self._init_alarm() # Should set the alarm for the next day
        if self.alarm_callback is not None:
            self.alarm_callback()

    def set_alarm_active(self, is_alarm_active: bool) -> None:
        self.alarm_active = is_alarm_active
        if self.alarm_active:
            self._init_alarm()
        elif self.alarm_timer is not None:
            self.alarm_timer.cancel()
            self.alarm_timer = None

    def set_alarm_callback(self, callback: Callable) -> None:
        self.alarm_callback = callback
        # Since we don't call the callback directly from the timer, we don't need to reinitialize.

    def _get_offset_time(self) -> int:
        # return time.gmtime() + self.current_time_offset
        return time.time() + self.current_time_offset

    def get_current_time_string(self, with_colon: bool = True):
        if with_colon:
            prestring = time.strftime('%H:%M', time.gmtime(self._get_offset_time()))
        else:
            prestring = time.strftime('%H %M', time.gmtime(self._get_offset_time()))
        # Rip one leading zero (eg 01:00 -> 1:00, but 00:00 -> 0:00)
        if prestring[0] == '0':
            prestring = ' ' + prestring[1:]  # Replace with space otherwise break monospace layout
        return prestring

    def get_alarm_time_string(self):
        time_components = self._get_time_from_minutes_through_day(self.alarm_time)
        return f'{time_components[0]:2d}:{time_components[1]:02d}'
    def get_alarm_active(self):
        return self.alarm_active
