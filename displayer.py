#!/usr/bin/python

# Caiden Wiley, 2024
# Adapted from template code from https://www.waveshare.com/product/displays/oled/1.51inch-transparent-oled.htm

'''
Components:
OLED screen (7 pins)
    - VCC -> 1 (3v3)
    - GND -> 14 (GND)
    - DIN -> 19 (GPIO 10)
    - CLK -> 23 (GPIO 11)
    - CS  -> 24 (GPIO 8)
    - DC  -> 22 (GPIO 25)
    - RST -> 13 (GPIO 27)
Amplifier (2 pins)
    - Vcc -> 4 (5v)
    - GND -> 6 (GND)
Rotary encoder (5 pins)
    - GND -> 25 (GND)
    -  +  -> 17 (3v3)
    - SW  -> 15 (GPIO 22)
    - CLK -> 12 (GPIO 18)
    - DT  -> 11 (GPIO 17)

Add the following to /boot/firmware/config.txt
    # Enable rotary encoder
    # CLK -> 12 (GPIO 18), DT -> 11 (GPIO 17)
    dtoverlay=rotary-encoder,pin_a=18,pin_b=17,relative_axis=-1,steps-per-period=2
    # Enable rotary encoder button
    # SW  -> 15 (GPIO 22)
    dtoverlay=gpio-key,gpio=22,keycode=28,label="ENTER"
'''


import sys
import os
assetdir = os.path.realpath('asset')
libdir = os.path.realpath('lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import time
import math
import OLED_1in51
import vlc
from PIL import Image,ImageDraw,ImageFont

# Dimensions of 1.5 inch transparent OLED screen
OLED_WIDTH   = 128
OLED_HEIGHT  = 64

# Default font location
FONT_RESOURCE = os.path.join(assetdir, 'noto_mono.ttf')

# Enables debug output
DEBUG_MODE = False

class Player:
    def __init__(self, url_list):
        self.url_list = url_list
        self.current_station = 0
        # self.current_url = self.url_list[self.current_station]
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.media = None
    
    def _current_url(self):
        return self.url_list[self.current_station]
    
    def _init_media(self):
        print("\n> Initializing media source: " + str(self._current_url()))
        self.media = self.instance.media_new(self._current_url())
        self.player.set_media(self.media)
    
    def play(self):
        if self.media == None:
            self._init_media()
        self.player.play()
    
    def pause(self):
        self.player.pause()
    
    def stop(self):
        self.player.stop()
        self.media = None
    
    def get_meta(self, e_meta):
        if self.media is None or self.media.get_meta(e_meta) is None:
            return 'Nothing!'
        else:
            return self.media.get_meta(e_meta)
    
    def get_title(self):
        return self.get_meta(vlc.Meta.Title)
    
    def get_now_playing(self):
        return self.get_meta(vlc.Meta.NowPlaying)
    
    def select_station(self, num):
        was_playing = self.player.is_playing()
        self.player.stop()
        # Loop index selecton if out of bounds.
        index = num % len(self.url_list)
        self.current_station = index
        self._init_media()
        if was_playing:
            self.play()
    
    def get_station_index(self):
        return self.current_station

def get_time_now_ms():
    return time.time_ns() // 1_000_000

def debug_print(text):
    if (DEBUG_MODE): print(text)

def generate_text_image(text: str, pos: tuple[int, int], font_size: int, image_in: Image = None) -> Image:
    debug_print("Generating text " + text + " at " + str(pos))
    if (image_in):
        image = image_in
    else:
        image = Image.new('1', (OLED_WIDTH, OLED_HEIGHT), "WHITE")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_RESOURCE, font_size)
    draw.text(pos, text, font = font, fill = 0)
    return image

# max_chars = number of characters to display at a given time, ie. effective width in characters.
# scroll_time_ms = time in ms to scroll 1 character width
# initial_time_ms = time in which the scroll started at the beginning
def generate_scrolling_text_image(text: str, pos: tuple[int, int], font_size: int, max_chars: int, scroll_speed_ms: int, initial_time_ms: int, image_in: Image = None) -> Image:
    # TODO generate text snippit based on input parameters
    overflow_size = len(text) - max_chars
    # If length of text fits within bounds, we don't need to do anything
    if overflow_size <= 0:
        return generate_text_image(text, pos, font_size, image_in=image_in)

    first_char_hold_add = 3
    last_char_hold_add = 3
    first_char_hold_ms = scroll_speed_ms * first_char_hold_add
    last_char_hold_ms = scroll_speed_ms * last_char_hold_add
    cycle_length_ms = first_char_hold_ms + overflow_size * scroll_speed_ms + last_char_hold_ms
    time_since_initial = get_time_now_ms() - initial_time_ms
    cycle_position_ms = time_since_initial % cycle_length_ms
    cycle_discrete = first_char_hold_add + overflow_size + last_char_hold_add
    cycle_index = math.floor((cycle_position_ms / cycle_length_ms) * cycle_discrete)
    char_index = min(max(cycle_index - first_char_hold_add, 0), overflow_size)

    truncated_text = text[char_index:char_index+max_chars]
    return generate_text_image(truncated_text, pos, font_size, image_in=image_in)

def wait(sec: int):
    time.sleep(sec)

def draw_image(disp: OLED_1in51, image: Image):
    image = image.rotate(180)
    disp.ShowImage(disp.getbuffer(image))

# TODO: Add other state info (station #, alarm set, alarm going off, mode)
def generate_clock_hud_image(time: str, track: str, station: int, start_time: int = 0) -> Image:
    station_str = (3 - len(str(station)))*"0" + str(station)
    clock = generate_text_image(time, (5, 0), 35)
    add_track_name = generate_scrolling_text_image(track, (31, 45), 10, 13, 300, start_time, image_in=clock)
    add_station_number = generate_text_image(station_str, (5, 45), 10, image_in=add_track_name)
    draw = ImageDraw.Draw(add_station_number)
    draw.line([(27, 42), (27, 58)], None, 1)
    return add_station_number
    

# Initialize Player object with station list
url_list_file = 'stations.list'
with open(url_list_file, 'r') as file:
    url_list = [line.strip() for line in file]
print(url_list)
player = Player(url_list)
player.select_station(2)

# TODO: Only update screen when a change in the display variables is detected
try:
    disp = OLED_1in51.OLED_1in51()
    disp.Init()
    disp.clear()

    player.play()

    last_track_name = player.get_now_playing()
    start_time = get_time_now_ms()
    while True:
        clock_time = time.strftime("%H:%M", time.localtime())
        track_name = player.get_now_playing()
        station_number = player.get_station_index()

        # Restart the scroll if title changes
        if track_name != last_track_name:
            start_time = get_time_now_ms()
            last_track_name = track_name

        hud_image = generate_clock_hud_image(clock_time, track_name, station_number)
        draw_image(disp, hud_image)
        # wait(0.1)
    
    # Shut down
    disp.clear()

except IOError as e:
    print(e)
    
except KeyboardInterrupt:    
    print("ctrl + c:")
    disp.module_exit()