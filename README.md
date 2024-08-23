# NetRadioBox
Net Radio Box is a small project by (me) aiming to replicate the functionality of a radio alarm clock.
I used to love being woken up by WETA every morning, but ever since we moved house I haven't been able to pick up any signals on my conventional radio alarm clock. I don't want to be woken up by loud static every morning.

### Parts list

Currently, the Net Radio Box is designed with
  - 1x Raspberry Pi 3B
  - 1x 5w+5w audio amplifier board [Amazon Link](https://www.amazon.com/Amplifier-DROK-PAM8406-Digital-Channel/dp/B077MKQJW2)
  - 2x 2in 5w speakers [Amazon Link](https://www.amazon.com/dp/B081169PC5)
  - 1x KY040 Rotary Encoder [Amazon Link](https://www.amazon.com/Cylewet-Encoder-15%C3%9716-5-Arduino-CYT1062/dp/B06XQTHDRR) (I got mine from somewhere else but they should be the same)
  - 1x 1.51in Transparent OLED from Waveshare [Amazon Link](https://www.amazon.com/Raspberry-1-51-Transparent-OLED-Interfaces/dp/B0B9L41TLK/)
  - Case / shell TBD.

The screen choice is silly, and I am unsure how it will affect the final physical design. It was chosen because it looked cool.

### Enable Overlay

This project requires a Raspberry Pi Overlay to be enabled in a separate configuration file, so this code isn't plug-n-play yet. I am unfamiliar with how the overlay system works, and whether the devices that end up representing the rotary encoder are the same every time. When I get my hands on another Raspberry Pi to test this, I will update this section.

For now, add the following to /boot/firmware/config.txt (or /boot/config.txt if on an older OS version):
```
# Enable rotary encoder
# CLK -> 12 (GPIO 18), DT -> 11 (GPIO 17)
dtoverlay=rotary-encoder,pin_a=18,pin_b=17,relative_axis=1,steps-per-period=2
# Enable rotary encoder button
# SW  -> 15 (GPIO 22)
dtoverlay=gpio-key,gpio=22,keycode=28,label="ENTER"
```
Reboot after you modify the config file for the changes to take effect.

The comments indicate the pins used for the rotary encoder. These are the GPIO pin numbers, not the physical pin numbers. More about my pin layout in the next section.
The switch on the KY040 is bound to the "ENTER" key because this is how it was done on a tutorial I was following. In practice I'm sure it could be any key, as long as you change the python code to match.

### Pins
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
  -  \+  -> 17 (3v3)
  - SW  -> 15 (GPIO 22)
  - CLK -> 12 (GPIO 18)
  - DT  -> 11 (GPIO 17)

### Code
After cloning the repo, install the requirements in a venv. 
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python radio.py
```

That should be all you need!
