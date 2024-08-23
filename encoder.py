import sys
import os
assetdir = os.path.realpath('asset')
libdir = os.path.realpath('lib')
if os.path.exists(libdir):
    sys.path.append(libdir)

import asyncio
import math
import evdev
import time
import threading
import OLED_1in51
import vlc
from PIL import Image,ImageDraw,ImageFont


'''
Add the following to /boot/firmware/config.txt
    # Enable rotary encoder
    # CLK -> 12 (GPIO 18), DT -> 11 (GPIO 17)
    dtoverlay=rotary-encoder,pin_a=18,pin_b=17,relative_axis=1,steps-per-period=2
    # Enable rotary encoder button
    # SW  -> 15 (GPIO 22)
    dtoverlay=gpio-key,gpio=22,keycode=28,label="ENTER"

The following is the device data for the different devices created by this configuration.
I don't know if the /dev/input/eventX will change based on platform or other factors.
    device /dev/input/event3, name "rotary@12", phys ""
    device /dev/input/event0, name "button@16", phys "gpio-keys/input0"
'''

# In case these settings need to be changed.
ROTARY_BUTTON_KEYCODE = 28
BUTTON_LONG_PRESS_DURATION_MS = 1000

# Dimensions of 1.5 inch transparent OLED screen
OLED_WIDTH   = 128
OLED_HEIGHT  = 64

# Default font location
FONT_RESOURCE = os.path.join(assetdir, 'noto_mono.ttf')

def get_time_now_ms():
    return time.time_ns() // 1_000_000

class RotaryEncoder:
    # Constructor inputs are device paths, eg, '/dev/input/event3'
    def __init__(self, rotary_device, rotary_button_device, rotate_left_callback, rotate_right_callback, button_callback, button_long_callback):
        self.button_callback = button_callback
        self.button_long_callback = button_long_callback
        self.rotate_left_callback = rotate_left_callback
        self.rotate_right_callback = rotate_right_callback

        self.button = False
        self.button_start_time = 0
        self.button_timer = None
        
        self.rotary_device = evdev.InputDevice(rotary_device)
        self.rotary_button_device = evdev.InputDevice(rotary_button_device)
    
    async def start(self):
        await asyncio.gather(
            self.handle_rotation(self.rotary_device),
            self.handle_button(self.rotary_button_device)
        )
        
    async def handle_rotation(self, device):
        async for event in device.async_read_loop():
            if event.type != 2: # REL_X
                continue
            if event.value == 1:
                self.rotate_left_callback()
            if event.value == -1:
                self.rotate_right_callback()

    def _check_button_long(self):
        if self.button and get_time_now_ms() - self.button_start_time >= BUTTON_LONG_PRESS_DURATION_MS:
            self.button_start_time = 0
            self.button_long_callback()
            
    async def handle_button(self, device):
        async for event in device.async_read_loop():
            if event.code != ROTARY_BUTTON_KEYCODE:
                continue
            if event.value == 1:
                self.button = True
                self.button_start_time = get_time_now_ms()
                self.button_timer = threading.Timer(BUTTON_LONG_PRESS_DURATION_MS/1000, self._check_button_long)
                self.button_timer.start()
            else:
                if self.button == True:
                    # Button has just been depressed
                    # Timer will catch long presses, we only detect short here.
                    self.button_timer.cancel()
                    if get_time_now_ms() - self.button_start_time < BUTTON_LONG_PRESS_DURATION_MS:
                        self.button_callback()
                self.button = False
                self.button_start_time = 0


class UserInterface:
    def __init__(self):
        self.modes = ["time", "alarm", "station"]
        self.mode = "station" # time, alarm, station, mode
        self.highlighted_mode = self.mode
        self.time = 24246456 # ms n 24 h
        self.alarm = 0 # ms in 24h
        self.station = 0
        self.station_count = 0
        self.alarm_active = False
        self.station_active = False

        self.display = OLED_1in51.OLED_1in51()
        self.display.Init()
        self.display.clear()

    def button_short(self):
        print("button_short")
        if self.mode == "mode":
            self.mode = self.highlighted_mode
        else:
            self.mode = "mode"
    def button_long(self):
        print("button_long")
        if self.mode == "station":
            self.station_active != self.station_active
            # TODO: Toggle sound
        if self.mode == "alarm":
            self.alarm_active != self.alarm_active
            # TODO: Toggle alarm (Where does it activate?)
    def rotate_left(self):
        print("rotate_left")
        self.rotate(-1)
    def rotate_right(self):
        print("rotate_right")
        self.rotate(1)
    def rotate(self, direction):
        if self.mode == "mode":
            # We're switching the highlighted mode here
            # Hard coded because simple.
            if direction < 0:
                if self.highlighted_mode == "time": self.highlighted_mode = "station"
                if self.highlighted_mode == "alarm": self.highlighted_mode = "time"
                if self.highlighted_mode == "station": self.highlighted_mode = "alarm"
            if direction > 0:
                if self.highlighted_mode == "station": self.highlighted_mode = "time"
                if self.highlighted_mode == "time": self.highlighted_mode = "alarm"
                if self.highlighted_mode == "alarm": self.highlighted_mode = "station"
        if self.mode == "time":
            # TODO: Change time
            pass
        if self.mode == "alarm":
            # TODO: Change alarm time
            pass
        if self.mode == "station":
            self.station += direction
            if self.station < 0:
                self.station = self.station_count-1
            if self.station >= self.station_count:
                self.station = 0

    def _generate_text_image(self, text: str, pos: tuple[int, int], font_size: int, image_in: Image = Image.new('1', (OLED_WIDTH, OLED_HEIGHT), "WHITE")) -> Image:
        draw = ImageDraw.Draw(image_in)
        font = ImageFont.truetype(FONT_RESOURCE, font_size)
        draw.text(pos, text, font = font, fill = 0)
        return image_in
    
    def _generate_circle_image(self, box: tuple[tuple[int, int], tuple[int, int]], filled: bool, image_in: Image = Image.new('1', (OLED_WIDTH, OLED_HEIGHT), "WHITE")) -> Image:
        draw = ImageDraw.Draw(image_in)
        draw.ellipse(box, "WHITE" if filled else None, "WHITE")
        return image_in

    def _generate_box_image(self, box: tuple[tuple[int, int], tuple[int, int]], thickness: float, image_in: Image = Image.new('1', (OLED_WIDTH, OLED_HEIGHT), "WHITE")) -> Image:
        draw = ImageDraw.Draw(image_in)
        draw.rectangle(box, None, "WHITE", thickness)
        return image_in
    def _generate_scrolling_text_image(self, text: str, pos: tuple[int, int], font_size: int, max_chars: int, scroll_speed_ms: int, initial_time_ms: int, image_in: Image = None) -> Image:
        overflow_size = len(text) - max_chars
        # If length of text fits within bounds, we don't need to do anything
        if overflow_size <= 0:
            return self._generate_text_image(text, pos, font_size, image_in=image_in)

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
        return self._generate_text_image(truncated_text, pos, font_size, image_in=image_in)
        
    def draw(self, track_name: str, track_start_time: int):
        # draw clock
        wrapped_time = self.time % (24*60*60*1000)
        time_string = str(math.floor(wrapped_time / (60*60*1000))) + ":" + str(math.floor((wrapped_time % (60*60*1000)) / (60 * 1000)))
        clock = self._generate_text_image(time_string, (5, 0), 35)
        # draw station number
        station_number_string = (3 - len(str(self.station)))*"0" + str(self.station)
        add_station_number = self._generate_text_image(station_number_string, (5, 45), 10, image_in=clock)
        # draw divider
        draw = ImageDraw.Draw(add_station_number)
        draw.line([(27, 42), (27, 58)], None, 1)
        # draw station track
        add_track_name = self._generate_scrolling_text_image(track_name, (31, 45), 10, 13, 300, track_start_time, image_in=add_station_number)
        # draw top circle
        # TODO: Get circles to render
        add_top_circle = self._generate_circle_image(((100,10), (120, 20)), False, add_track_name)
        # draw middle circle    (filled in if alarm active)
        # draw bottom circle    (filled in if station active)
        # draw selection box
        # finalize image
        image = add_top_circle
        image = image.rotate(180)
        self.display.ShowImage(self.display.getbuffer(image))
        return
    
    def clear(self):
        self.display.clear()

    


# Ensures the async task runs forever
# Important for capturing the RotaryEncoder events
def run_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

total_stations = 67
selected_station = 0
def change_station(direciton):
    global selected_station
    selected_station += direciton
    if selected_station < 0:
        selected_station = total_stations-1
    if selected_station >= total_stations:
        selected_station = 0

ui = UserInterface()

# Runs alongside the RotaryEncoder thread
def main():
    try:
        global selected_station
        global ui
        print("Active")
        while True:
            ui.draw("test track", 0)
    finally:
        ui.clear()

# Sets up and runs RotaryEncoder in a separate thread
# This allows the callbacks :))
if __name__ == "__main__":
    # Create a new event loop
    new_loop = asyncio.new_event_loop()
    
    # Create and start a new thread to run the event loop
    loop_thread = threading.Thread(target=run_event_loop, args=(new_loop,))
    loop_thread.start()
    
    # Create and schedule the async task
    enc = RotaryEncoder('/dev/input/event3', '/dev/input/event0', ui.rotate_left, ui.rotate_right, ui.button_short, ui.button_long)
    asyncio.run_coroutine_threadsafe(enc.start(), new_loop)
    
    # Run other tasks in the main thread
    main()

# # self.value = min(max(self.min, self.value + event.value), self.max)
# print(device.path, evdev.categorize(event), sep=': ')
# print(repr(event))
# # print(dir(event))
# print(event.code, event.sec, event.timestamp, event.type, event.usec, event.value, sep=' | ')
