"""Radio class"""

import threading
from mode_enum import Mode
from user_interface_class import UserInterface
from player_class import Player
from clock_class import Clock

# Clock blinking
CLOCK_BLINK_ON_MS = 500
CLOCK_BLINK_OFF_MS = 500

COLON_BLINK_ON_MS = 1000
COLON_BLINK_OFF_MS = 1000

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

        self.clock.set_alarm_callback(self.active_alarm)

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

    def active_alarm(self):
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