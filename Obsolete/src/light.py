#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
https://docs.elephantrobotics.com/docs/gitbook-en/7-ApplicationBasePython/7.7_example.html#1-controlling-rgb-light-panel

This script controls the LED light on a MyCobot robot using the pymycobot library.
The script initializes a MyCobot instance using the Raspberry Pi port and baud rate.
It then enters a loop that runs 7 times, changing the LED light color on the MyCobot
to blue, red, and green with a 2-second interval between each color change.
Classes:
    MyCobot: Represents the MyCobot robot.
Variables:
    PI_PORT (str): The serial port for the Raspberry Pi version of MyCobot.
    PI_BAUD (int): The baud rate for the Raspberry Pi version of MyCobot.
    mc (MyCobot): An instance of the MyCobot class initialized with PI_PORT and PI_BAUD.
    i (int): Loop counter, initialized to 7.
Functions:
    mc.set_color(r, g, b): Sets the LED color on the MyCobot robot.
    time.sleep(seconds): Pauses execution for the specified number of seconds.
Usage:
    Run the script to cycle the MyCobot LED light through blue, red, and green colors
    with a 2-second interval, repeating the cycle 7 times.
"""

from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD

import time

# MyCobot class initialization requires two parameters:
#   The first is the serial port string, such as:
#       linux: "/dev/ttyUSB0"
#          or  "/dev/ttyAMA0"
#       windows: "COM3"
#   The second is the baud rate:
#       M5 version is: 115200
#
#    Example:
#       mycobot-M5:
#           linux:
#              mc = MyCobot("/dev/ttyUSB0", 115200)
#          or  mc = MyCobot("/dev/ttyAMA0", 115200)
#           windows:
#              mc = MyCobot("COM3", 115200)
#       mycobot-raspi:
#           mc = MyCobot(PI_PORT, PI_BAUD)


def main():
    mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

    i = 7
    # loop 7 times
    while i > 0:
        mc.set_color(0, 0, 255) # blue light on
        time.sleep(2)           # wait for 2 seconds
        mc.set_color(255, 0, 0) # red light on
        time.sleep(2)           # wait for 2 seconds
        mc.set_color(0, 255, 0) # green light on
        time.sleep(2)           # wait for 2 seconds
        i -= 1


if __name__ == "__main__":
    main()
