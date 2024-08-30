"""
Provides an interface for the rotary encoder and button.
All callbacks must be set before starting the encoder threads with Encoder.start().
Two looping threads execute the appropriate callback functions when the corresponding events occur.
"""

import evdev
import threading
from typing import Callable
from constants import time_now

# Devices
ROTARY_ENCODER_DEVICE = '/dev/input/event3'
ROTARY_ENCODER_BUTTON_DEVICE = '/dev/input/event0'
BUTTON_LONG_PRESS_DURATION_MS = 800
ROTARY_BUTTON_KEYCODE = 28

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

    def _make_daemon_thread(self, function: Callable) -> None:
        thread = threading.Thread(target=function)
        thread.daemon = True
        thread.start()
        return thread

    def start(self) -> None:
        # Note: read_loop is blocking! That's why it has to be run in its own thread
        self.rotation_thread = self._make_daemon_thread(lambda: self.handle_rotation(self.rotary_device))
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

    def set_rotate_left_callback(self, callback: Callable) -> None:
        self.rotate_left_callback = callback
    def set_rotate_right_callback(self, callback: Callable) -> None:
        self.rotate_right_callback = callback
    def set_button_short_callback(self, callback: Callable) -> None:
        self.button_short_callback = callback
    def set_button_long_callback(self, callback: Callable) -> None:
        self.button_long_callback = callback