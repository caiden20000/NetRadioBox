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


##########
### Constants
##########

# Dimensions of 1.5 inch transparent OLED screen
OLED_WIDTH   = 128
OLED_HEIGHT  = 64

# Default font location
FONT_RESOURCE = os.path.join(assetdir, 'noto_mono.ttf')


##########
### Utility functions
##########

# Gets the current time in ms
# MS is the default representation of all integer times in this program.
def time_now() -> int:
    return time.time_ns() // 1_000_000


##########
### Classes
##########

class Mode(Enum):
    STATION = 1
    TIME = 2
    ALARM = 3
    MODE = 4


# Call set functions to update the UI.
# The UI does not modify external state.
class UserInterface:
    def __init__(self):
        self.track_name = ""
        self.time = ""
        self.station_number = ""
        self.selected_mode = Mode.STATION
        self.alarm_active = False
        self.station_active = False

        self.track_start_time = 0

        self.display = OLED_1in51.OLED_1in51()
        self.display.Init()
        self.display.clear()

    def _get_scrolling_track_name(self, max_chars: int, scroll_speed: int = 300, ends_hold_multiple: int = 3):
        overflow_size = len(self.track_name) - max_chars
        # If length of text fits within bounds, we don't need to do anything
        if overflow_size <= 0:
            return self.track_name

        cycle_length = (scroll_speed * ends_hold_multiple * 2) + (overflow_size * scroll_speed)
        cycle_position = (time_now() - self.track_start_time) % cycle_length
        cycle_discrete = ends_hold_multiple*2 + overflow_size
        cycle_index = math.floor((cycle_position / cycle_length) * cycle_discrete)
        char_index = min(max(cycle_index - ends_hold_multiple, 0), overflow_size)

        truncated_track_name = self.track_name[char_index:char_index+max_chars]
        return truncated_track_name
    
    def set_track_name(self, new_track_name: str) -> None:
        if new_track_name == self.track_name:
            return
        self.track_name = new_track_name
        self.track_start_time = time_now()
        self.draw_ui()

    def set_time(self, new_time: str) -> None:
        self.time = new_time
        self.draw_ui()

    def set_station_number(self, new_station_number: int) -> None:
        padded_number = str(new_station_number).zfill(3)
        self.station_number = padded_number
        self.draw_ui()

    def set_selected_mode(self, new_mode: Mode) -> None:
        self.selected_mode = new_mode
        self.draw_ui()

    def set_alarm_active(self, is_alarm_active: bool) -> None:
        self.alarm_active = is_alarm_active
        self.draw_ui()

    def set_station_active(self, is_station_active: bool) -> None:
        self.station_active = is_station_active
        self.draw_ui()

    def clear(self):
        self.display.clear()

    def draw_ui(self):
        image = Image.new('1', (OLED_WIDTH, OLED_HEIGHT), "WHITE")
        draw = ImageDraw.Draw(image)
        time_font = ImageFont.truetype(FONT_RESOURCE, 35)
        station_font = ImageFont.truetype(FONT_RESOURCE, 10)

        # Draw time
        draw.text(self.time, (5, 0), font = time_font, fill = 0)
        # Draw station number
        draw.text(self.station_number, (5, 45), font = station_font, fill = 0)
        # Draw separator
        draw.line([(27, 42), (27, 58)], None, 1)
        # Draw track name
        scrolled_track_name = self._get_scrolling_track_name(13, 300)
        draw.text(self.station_number, (31, 45), font = station_font, fill = 0)
        # Draw modes
        # TODO: Draw the mode circles
        # TODO: Fill in the circles that are activated
        # Draw mode selection box
        # TODO: Draw the mode selection box around correct circle

        # Render drawings onto screen
        image = image.rotate(180)
        self.display.ShowImage(self.display.getbuffer(image))


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

    

