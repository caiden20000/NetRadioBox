"""Main code runner"""
from radio_class import Radio
from encoder_class import Encoder

radio = Radio()
encoder = Encoder()

encoder.set_rotate_left_callback(radio.control_left)
encoder.set_rotate_right_callback(radio.control_right)
encoder.set_button_short_callback(radio.control_short_click)
encoder.set_button_long_callback(radio.control_long_click)

encoder.start()

# Get station list from "station.list" and set it in the player
URL_LIST_FILE = 'station.list'
with open(URL_LIST_FILE, 'r', encoding='utf-8') as file:
    url_list = [line.strip() for line in file]
print("Initializing with station list: ", url_list)
radio.player.set_station_list(url_list)

try:
    while True:
        radio.update()
finally:
    radio.ui.clear()
