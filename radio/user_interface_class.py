"""
User interface class for the radio.
"""

import threading
import os
import math
import lib.OLED_1in51 as OLED_1in51
from PIL import Image, ImageDraw, ImageFont
from constants import time_now
from mode_enum import Mode

# Dimensions of 1.5 inch transparent OLED screen
OLED_WIDTH   = 128
OLED_HEIGHT  = 64

# Screen update speed
SCREEN_FRAME_UPDATE_DURATION_MS = 150

# Default font location
# assetdir = os.path.realpath('asset') # For fonts
# FONT_RESOURCE = os.path.join(assetdir, 'noto_mono.ttf')
FONT_RESOURCE = os.path.join(os.path.dirname(__file__), 'asset/noto_mono.ttf')


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

        self.last_draw = time_now()
        self.update_timer = None

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

    def _schedule_draw(self, image: Image):
        if self.update_timer is not None:
            self.update_timer.cancel()
        # If it has been long enough since the last frame, draw the image.
        if time_now() - self.last_draw >= SCREEN_FRAME_UPDATE_DURATION_MS:
            self.display.ShowImage(self.display.getbuffer(image))
            self.last_draw = time_now()
        # Otherwise, come back in X ms to try again.
        else:
            time_left = SCREEN_FRAME_UPDATE_DURATION_MS - (time_now() - self.last_draw)
            self.update_timer = threading.Timer(time_left / 1000, lambda: self._schedule_draw(image))
            self.update_timer.start()


    def draw_ui(self):
        # Prevent redrawing identical content
        if self.update_required is False:
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
        if self.selected_mode == Mode.STATION:
            draw.line([(115, 12), (115, 14)], None, 3 if self.highlight_selector else 1)
        if self.selected_mode == Mode.TIME:
            draw.line([(115, 27), (115, 29)], None, 3 if self.highlight_selector else 1)
        if self.selected_mode == Mode.ALARM:
            draw.line([(115, 42), (115, 44)], None, 3 if self.highlight_selector else 1)
        # Render drawings onto screen
        image = image.rotate(180)
        self._schedule_draw(image)