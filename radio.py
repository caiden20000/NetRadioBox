# Caiden Wiley, Aug 2024

''' Architecture
Class UserInterface
    - Controls the screen
    - Abstracts drawing
    - Takes in text and numbers to modify the UI
    - Changes on update to values
Class Player
    - Controls audio via VLC library
    - Maintains list of stations
    - Abstracts switching stations
    - Exposes station information
Class Encoder
    - Captures event data from rotary_encoder device
    - Captures "enter" key presses from rotary_encoder button
    - Exposes callbacks for each event type
    - Will run on separate thread
Class Clock
    - Keeps track of the time representations
    - Has current time and alarm time
    - Abstracts setting of time (delta change in minutes)
    - Controls enabling/disabling of alarm
Class Radio
    - Aggregates UserInterface, Player, and Clock classes
    - Controls UserInterface with data from Player and Clock
    - Exposes UI-control level functions (What a user would activate via button)
    - Controls mode-based control

Questions:
Who controls the mode?
    A: Radio class
What indicates we are in mode-selecting mode?
    A: Thicker selection box

The radio class needs to take care of
'''


import sys, os
assetdir = os.path.realpath('asset') # For fonts
libdir = os.path.realpath('lib')     # For OLED_1in51.py 
if os.path.exists(libdir):
    sys.path.append(libdir)

import asyncio, math, evdev, time, threading, vlc
import OLED_1in51 # Located in libdir
from PIL import Image,ImageDraw,ImageFont
from enum import Enum


class Mode(Enum):
    STATION = 1
    TIME = 2
    ALARM = 3
    MODE = 4

# Call set functions to update the UI.
# The UI does not modify external state.
class UserInterface:
    def __init__(self):
        pass
    
    def set_track_name(self, new_track_name: str) -> None:
        pass

    def set_time(self, new_time: str) -> None:
        pass

    def set_station_number(self, new_station_number: int) -> None:
        pass

    def set_selected_mode(self, new_mode: Mode) -> None:
        pass

    def set_alarm_active(self, is_alarm_active: bool) -> None:
        pass

    def set_station_active(self, is_station_active: bool) -> None:
        pass

    def draw_ui(self):
        pass


class Player:
    def __init__(self):
        pass
    
    def play(self) -> bool:
        pass

    def stop(self) -> bool:
        pass

    def set_station(self, new_station: int) -> bool:
        pass

    def scrub_station(self, distance: int) -> None:
        pass

    def get_station_number(self) -> int:
        pass
    def get_station_title(self) -> str:
        pass
    def get_station_track(self) -> str:
        pass
    def get_station_count(self) -> int:
        pass
    


class Encoder:
    def __init__(self):
        pass

    def set_rotate_left_callback(self, callback: function) -> None:
        pass
    def set_rotate_right_callback(self, callback: function) -> None:
        pass
    def set_button_short_callback(self, callback: function) -> None:
        pass
    def set_button_long_callback(self, callback: function) -> None:
        pass



# TODO: Determine how we will store time (ms, seconds?)
class Clock:
    def __init__(self):
        pass

    def set_time_to_system_time(self) -> None:
        pass
    def set_time(self, time: int) -> None:
        pass
    def scrub_time(self, distance: int) -> None:
        pass
    def set_alarm_time(self, time: int) -> None:
        pass
    def scrub_alarm_time(self, distance: int) -> None:
        pass
    def set_alarm_active(self, is_alarm_active: bool) -> None:
        pass
    def set_alarm_callback(self, callback: function) -> None:
        pass


# TODO: Public methods
class Radio:
    def __init__(self):
        pass

    def control_left(self):
        pass
    def control_right(self):
        pass
    def control_short_click(self):
        pass
    def control_long_click(self):
        pass

    

