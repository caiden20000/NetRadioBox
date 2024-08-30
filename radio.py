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
from types import FunctionType as function
from datetime import datetime, timedelta

# TODO: Mode resets to station after amount of time
# TODO: Auto timezone support based on wifi location

# BUG: Several events will queue. This is an issue because turning the encoder can be very fast,
#      and all the events will be queued up despite the user not turning the encoder anymore.

##########
### Constants
##########

# Dimensions of 1.5 inch transparent OLED screen
OLED_WIDTH   = 128
OLED_HEIGHT  = 64

# Default font location
FONT_RESOURCE = os.path.join(assetdir, 'noto_mono.ttf')

# Devices
ROTARY_ENCODER_DEVICE = '/dev/input/event3'
ROTARY_ENCODER_BUTTON_DEVICE = '/dev/input/event0'
BUTTON_LONG_PRESS_DURATION_MS = 800
ROTARY_BUTTON_KEYCODE = 28

# Clock blinking
CLOCK_BLINK_ON_MS = 500
CLOCK_BLINK_OFF_MS = 500

COLON_BLINK_ON_MS = 1000
COLON_BLINK_OFF_MS = 1000

# Screen update speed
SCREEN_FRAME_UPDATE_DURATION_MS = 150

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
        self.highlight_selector = False
        self.alarm_active = False
        self.station_active = False

        self.track_start_time = 0

        self.display = OLED_1in51.OLED_1in51()
        self.display.Init()
        self.display.clear()

        self.update_required = True
        self.scroll_speed = 300
        self.max_chars = 13
        self.update_schedule_timer = None

    def _get_scrolling_track_name(self, max_chars: int = 13, scroll_speed: int = 300, ends_hold_multiple: int = 3):
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
        self._update_schedule()

    def _update_schedule(self):
        self.update_required = True
        if self.update_schedule_timer is not None:
            self.update_schedule_timer.cancel()
        if len(self.track_name) > self.max_chars:
            # We are scrolling, so we need to update the schedule thread
            self.update_schedule_timer = threading.Timer(self.scroll_speed / 1000, self._update_schedule)
            self.update_schedule_timer.start()
        self.draw_ui()

    def set_time(self, new_time: str) -> None:
        if self.time == new_time:
            return
        self.time = new_time
        self.update_required = True

    def set_station_number(self, new_station_number: int) -> None:
        padded_number = str(new_station_number).zfill(3)
        if self.station_number == padded_number:
            return
        self.station_number = padded_number
        self.update_required = True

    def set_selected_mode(self, new_mode: Mode) -> None:
        if self.selected_mode == new_mode:
            return
        self.selected_mode = new_mode
        self.update_required = True

    def set_alarm_active(self, is_alarm_active: bool) -> None:
        if self.alarm_active == is_alarm_active:
            return
        self.alarm_active = is_alarm_active
        self.update_required = True

    def set_station_active(self, is_station_active: bool) -> None:
        if self.station_active == is_station_active:
            return
        self.station_active = is_station_active
        self.update_required = True
    
    def set_highlight_selector(self, highlight: bool) -> None:
        if self.highlight_selector == highlight:
            return
        self.highlight_selector = highlight
        self.update_required = True

    def clear(self):
        self.display.clear()

    def draw_ui(self):
        # Prevent redrawing identical content
        if self.update_required == False:
            return
        self.update_required = False
        print("Draw_ui called: UPDATING screen!")

        image = Image.new('1', (OLED_WIDTH, OLED_HEIGHT), "WHITE")
        draw = ImageDraw.Draw(image)
        time_font = ImageFont.truetype(FONT_RESOURCE, 35)
        station_font = ImageFont.truetype(FONT_RESOURCE, 10)

        # Draw time
        draw.text((5, 0), self.time, font = time_font, fill = 0)
        # Draw station number
        draw.text((5, 45), self.station_number, font = station_font, fill = 0)
        # Draw separator
        draw.line([(27, 42), (27, 58)], None, 1)
        # Draw track name
        scrolled_track_name = self._get_scrolling_track_name()
        draw.text((31, 45), scrolled_track_name, font = station_font, fill = 0)
        # Draw modes
        draw.ellipse([(120, 10), (126, 16)], "WHITE", 0, 6 if self.station_active else 1) # Station Mode
        draw.ellipse([(120, 25), (126, 31)], "WHITE", 0, 1) # Time Mode
        draw.ellipse([(120, 40), (126, 46)], "WHITE", 0, 6 if self.alarm_active else 1) # Alarm Mode
        # Draw mode selection box
        if self.selected_mode == Mode.STATION: draw.line([(115, 12), (115, 14)], None, 3 if self.highlight_selector else 1)
        if self.selected_mode == Mode.TIME:    draw.line([(115, 27), (115, 29)], None, 3 if self.highlight_selector else 1)
        if self.selected_mode == Mode.ALARM:   draw.line([(115, 42), (115, 44)], None, 3 if self.highlight_selector else 1)
        # Render drawings onto screen
        image = image.rotate(180)
        self.display.ShowImage(self.display.getbuffer(image))


class Player:
    def __init__(self, station_list: list[str] = []):
        self.station_list = station_list
        self.current_station_number = 0
        self.is_playing = False
        # VLC related attributes
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media = None

    def _init_media(self, url: str) -> None:
        self.media = self.instance.media_new(url)
        self.player.set_media(self.media)

    def _get_meta(self, e_meta: vlc.Meta) -> str:
        if self.media is None or self.media.get_meta(e_meta) is None:
            return 'unknown'
        else:
            return self.media.get_meta(e_meta)

    def set_station_list(self, station_list: list[str]) -> None:
        self.station_list = station_list
    
    def play(self) -> None:
        print("Player starting playback")
        if self.media is None:
            self._init_media(self.station_list[self.current_station_number])
        self.player.play()
        self.is_playing = True

    def stop(self) -> None:
        print("Player stopping playback")
        self.player.stop()
        self.media = None
        self.is_playing = False

    def set_station(self, new_station_number: int) -> bool:
        if new_station_number < 0 or new_station_number >= len(self.station_list):
            return False
        if self.is_playing: self.player.stop()
        self.current_station_number = new_station_number
        self._init_media(self.station_list[new_station_number])
        if self.is_playing: self.player.play()
        print("Now playing station ", self.current_station_number)
        return True

    def scrub_station(self, distance: int) -> None:
        wrapped_station_number = (self.current_station_number + distance) % len(self.station_list)
        self.set_station(wrapped_station_number)

    def get_station_number(self) -> int:
        return self.current_station_number
    def get_station_title(self) -> str:
        return self._get_meta(vlc.Meta.Title)
    def get_station_track(self) -> str:
        return self._get_meta(vlc.Meta.NowPlaying)
    def get_station_count(self) -> int:
        return len(self.station_list)
    

class Encoder:
    def __init__(self):
        self.button_short_callback = None
        self.button_long_callback = None
        self.rotate_left_callback = None
        self.rotate_right_callback = None

        self.button = False
        self.button_start_time = 0
        self.button_timer = None
        
        self.rotary_device = evdev.InputDevice(ROTARY_ENCODER_DEVICE)
        self.rotary_button_device = evdev.InputDevice(ROTARY_ENCODER_BUTTON_DEVICE)

        self.rotation_thread = None
        self.button_thread = None

    def _make_daemon_thread(self, function: function) -> None:
        thread = threading.Thread(target=function)
        thread.daemon = True
        thread.start()
        return thread
    
    def start(self) -> None:
        # Note: read_loop is blocking! That's why it has to be run in its own thread
        self.rotatation_thread = self._make_daemon_thread(lambda: self.handle_rotation(self.rotary_device))
        self.button_thread = self._make_daemon_thread(lambda: self.handle_button(self.rotary_button_device))

    def handle_rotation(self, device: evdev.InputDevice) -> None:
        for event in device.read_loop():
            if event.type != 2: # 2 is REL_X type event, the rotation of the encoder
                continue
            if event.value == 1:
                self.rotate_right_callback()
            if event.value == -1:
                self.rotate_left_callback()

    def _check_button_long(self) -> None:
        if self.button and time_now() - self.button_start_time >= BUTTON_LONG_PRESS_DURATION_MS:
            self.button_start_time = 0
            self.button_long_callback()
            
    def handle_button(self, device) -> None:
        for event in device.read_loop():
            if event.code != ROTARY_BUTTON_KEYCODE:
                continue
            if event.value == 1:
                self.button = True
                self.button_start_time = time_now()
                self.button_timer = threading.Timer(BUTTON_LONG_PRESS_DURATION_MS/1000, self._check_button_long)
                self.button_timer.start()
            else:
                if self.button == True:
                    # Button has just been depressed
                    # Timer will catch long presses, we only detect short here.
                    self.button_timer.cancel()
                    if time_now() - self.button_start_time < BUTTON_LONG_PRESS_DURATION_MS:
                        self.button_short_callback()
                self.button = False
                self.button_start_time = 0

    def set_rotate_left_callback(self, callback: function) -> None:
        self.rotate_left_callback = callback
    def set_rotate_right_callback(self, callback: function) -> None:
        self.rotate_right_callback = callback
    def set_button_short_callback(self, callback: function) -> None:
        self.button_short_callback = callback
    def set_button_long_callback(self, callback: function) -> None:
        self.button_long_callback = callback



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

    def set_alarm_callback(self, callback: function) -> None:
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

class Radio:
    def __init__(self):
        self.mode = Mode.STATION
        self.highlighted_mode = Mode.STATION
        self.station_active = False
        self.alarm_active = False

        self.track_name = "Sound off"

        self.ui = UserInterface()
        self.clock = Clock()
        self.player = Player()

        self.clock.set_alarm_callback(self.alarm_active)

        self.clock_blink_timer = None
        self.clock_blink_enabled = False
        self.clock_blink_faceon = True

        self.colon_blink_timer = None
        self.colon_blink_enabled = False
        self.colon_blink_faceon = True

        self._sync_ui()
    
    def _enable_clock_blink(self):
        self.clock_blink_enabled = True
        # Initialize to false b/c _clock_blink_schedule inverts initially.
        self.clock_blink_faceon = False
        self._clock_blink_schedule()
    def _disable_clock_blink(self):
        self.clock_blink_enabled = False
        if self.clock_blink_timer is not None:
            self.clock_blink_timer.cancel()
            self.clock_blink_timer = None
    
    def _clock_blink_schedule(self):
        if self.clock_blink_timer is not None:
            self.clock_blink_timer.cancel()
        if self.clock_blink_enabled is False:
            return
        self.clock_blink_faceon = not self.clock_blink_faceon
        if self.clock_blink_faceon:
            if self.highlighted_mode == Mode.TIME:
                self.ui.set_time(self.clock.get_current_time_string())
            elif self.highlighted_mode == Mode.ALARM:
                self.ui.set_time(self.clock.get_alarm_time_string())
            else:
                print("Bug: Clock blinking when not in Time or Alarm mode!")
        else:
            self.ui.set_time("  :  ")
        self.ui.draw_ui()
        if self.clock_blink_faceon:
            self.clock_blink_timer = threading.Timer(CLOCK_BLINK_ON_MS / 1000, self._clock_blink_schedule)
        else:
            self.clock_blink_timer = threading.Timer(CLOCK_BLINK_OFF_MS / 1000, self._clock_blink_schedule)
        self.clock_blink_timer.start()
    
    ### The following 3 methods are basically copies of the above 3.

    def _enable_colon_blink(self):
        self.colon_blink_enabled = True
        # Initialize to false b/c _colon_blink_schedule inverts initially.
        self.colon_blink_faceon = False
        self._colon_blink_schedule()
    def _disable_colon_blink(self):
        self.colon_blink_enabled = False
        if self.colon_blink_timer is not None:
            self.colon_blink_timer.cancel()
            self.colon_blink_timer = None
    
    def _colon_blink_schedule(self):
        if self.colon_blink_timer is not None:
            self.colon_blink_timer.cancel()
        if self.colon_blink_enabled is False:
            return
        self.colon_blink_faceon = not self.colon_blink_faceon

        if self.highlighted_mode == Mode.STATION:
            self.ui.set_time(self.clock.get_current_time_string(self.colon_blink_faceon))
        else:
            print("Bug: Colon blinking when not in STATION mode!")

        self.ui.draw_ui()
        print("DEBUG: Colon blink faceon: ", self.colon_blink_faceon)
        if self.colon_blink_faceon:
            self.colon_blink_timer = threading.Timer(COLON_BLINK_ON_MS / 1000, self._colon_blink_schedule)
        else:
            self.colon_blink_timer = threading.Timer(COLON_BLINK_OFF_MS / 1000, self._colon_blink_schedule)
        self.colon_blink_timer.start()

    def alarm_active(self):
        print(">>>>> Playing station due to alarm")
        self.station_active = True
        self.player.play()
        self.ui.set_station_active(True)
        self.ui.draw_ui()

    # In MODE mode, scrubs highlighted mode left & update UI
    # In STATION mode, scrubs station number left & update UI
    # In TIME mode, scrubs current clock time left & update UI
    # In ALARM mode, scrubs alarm clock time left & update UI
    def control_left(self):
        print("DEBUG: control_left")
        if self.mode == Mode.MODE:
            if self.highlighted_mode == Mode.STATION: self.highlighted_mode = Mode.ALARM
            elif self.highlighted_mode == Mode.TIME:  self.highlighted_mode = Mode.STATION
            elif self.highlighted_mode == Mode.ALARM: self.highlighted_mode = Mode.TIME

            if self.highlighted_mode == Mode.TIME or self.highlighted_mode == Mode.ALARM:
                self._enable_clock_blink()
                self._disable_colon_blink()
                if self.highlighted_mode == Mode.ALARM: self.ui.set_time(self.clock.get_alarm_time_string())
                else: self.ui.set_time(self.clock.get_current_time_string())
            elif self.highlighted_mode == Mode.STATION:
                self._disable_clock_blink()
                self._enable_colon_blink()
            self.ui.set_selected_mode(self.highlighted_mode)

        if self.mode == Mode.STATION:
            self.player.scrub_station(-1)
            self.ui.set_station_number(self.player.get_station_number())

        if self.mode == Mode.TIME:
            self.clock.scrub_current_time_offset(-1)
            self._enable_clock_blink()
            self.ui.set_time(self.clock.get_current_time_string())

        if self.mode == Mode.ALARM:
            self.clock.scrub_alarm_time(-1)
            self._enable_clock_blink()
            self.ui.set_time(self.clock.get_alarm_time_string())
            
        
        self.ui.draw_ui()
    
    # In MODE mode, scrubs highlighted mode right & update UI
    # In STATION mode, scrubs station number right & update UI
    # In TIME mode, scrubs current clock time right & update UI
    # In ALARM mode, scrubs alarm clock time right & update UI
    def control_right(self):
        print("DEBUG: control_right")
        if self.mode == Mode.MODE:
            if self.highlighted_mode == Mode.STATION: self.highlighted_mode = Mode.TIME
            elif self.highlighted_mode == Mode.TIME:  self.highlighted_mode = Mode.ALARM
            elif self.highlighted_mode == Mode.ALARM: self.highlighted_mode = Mode.STATION

            if self.highlighted_mode == Mode.TIME or self.highlighted_mode == Mode.ALARM:
                self._enable_clock_blink()
                self._disable_colon_blink()
                if self.highlighted_mode == Mode.ALARM: self.ui.set_time(self.clock.get_alarm_time_string())
                else: self.ui.set_time(self.clock.get_current_time_string())
            elif self.highlighted_mode == Mode.STATION:
                self._disable_clock_blink()
                self._enable_colon_blink()
            self.ui.set_selected_mode(self.highlighted_mode)

        if self.mode == Mode.STATION:
            self.player.scrub_station(1)
            self.ui.set_station_number(self.player.get_station_number())

        if self.mode == Mode.TIME:
            self.clock.scrub_current_time_offset(1)
            self._enable_clock_blink()
            self.ui.set_time(self.clock.get_current_time_string())

        if self.mode == Mode.ALARM:
            self.clock.scrub_alarm_time(1)
            self._enable_clock_blink()
            self.ui.set_time(self.clock.get_alarm_time_string())

        self.ui.draw_ui()
    
    # In MODE mode, makes highlighted mode the active mode & update the UI
    # In ANY OTHER mode, makes current mode the highlighted mode, makes MODE mode the active mode, & update the UI
    def control_short_click(self):
        print("DEBUG: control_short_click")
        if self.mode == Mode.MODE:
            self.mode = self.highlighted_mode
            self.ui.set_highlight_selector(False)
        else:
            self.highlighted_mode = self.mode
            self.mode = Mode.MODE
            self.ui.set_highlight_selector(True)
        self.ui.draw_ui()

    # In MODE mode, does what the highlighted mode would do
    # In STATION mode, toggle the player on/off & update the UI
    # In ALARM mode, toggle the alarm on/off & update the UI
    # In TIME mode, resets the time to system time & update the UI
    def control_long_click(self):
        print("DEBUG: control_long_click")
        if self.highlighted_mode == Mode.STATION:
            self._toggle_player()
        if self.highlighted_mode == Mode.ALARM:
            self._toggle_alarm()
        if self.highlighted_mode == Mode.TIME:
            self.clock.set_time_to_system_time()
            self.ui.set_time(self.clock.get_current_time_string())
        self.ui.draw_ui()

    def _toggle_player(self) -> None:
        print("DEBUG: _toggle_player")
        self.station_active = not self.station_active
        self.ui.set_station_active(self.station_active)
        if self.station_active: self.player.play()
        else: self.player.stop()
    def _toggle_alarm(self) -> None:
        print("DEBUG: _toggle_alarm")
        self.alarm_active = not self.alarm_active
        self.ui.set_alarm_active(self.alarm_active)
        self.clock.set_alarm_active(self.alarm_active)
    
    def update(self) -> None:
        current_track_name = self.player.get_station_track()
        if self.track_name != current_track_name:
            self.track_name = current_track_name
            self.ui.set_track_name(self.track_name)
        if self.mode == Mode.TIME:
            self.ui.set_time(self.clock.get_current_time_string())
        if self.mode == Mode.ALARM:
            self.ui.set_time(self.clock.get_alarm_time_string())
        self.ui.draw_ui()
    
    def _sync_ui(self) -> None:
        self.ui.set_track_name(self.track_name)
        self.ui.set_time(self.clock.get_current_time_string())
        self.ui.set_station_number(self.player.get_station_number())
        self.ui.set_selected_mode(self.mode)
        self.ui.set_alarm_active(self.alarm_active)
        self.ui.set_station_active(self.station_active)



##########
### Main code
##########


radio = Radio()
encoder = Encoder()

encoder.set_rotate_left_callback(radio.control_left)
encoder.set_rotate_right_callback(radio.control_right)
encoder.set_button_short_callback(radio.control_short_click)
encoder.set_button_long_callback(radio.control_long_click)

encoder.start()

# Get station list from "station.list" and set it in the player
url_list_file = 'station.list'
with open(url_list_file, 'r') as file:
    url_list = [line.strip() for line in file]
print("Initializing with station list: ", url_list)
radio.player.set_station_list(url_list)

try:
    while True:
        radio.update()
finally:
    radio.ui.clear()