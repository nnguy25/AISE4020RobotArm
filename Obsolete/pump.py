#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This scripts demonstrates how to set up GPIO (General Purpose Input/Output)
with MyCobot.

https://docs.elephantrobotics.com/docs/gitbook-en/7-ApplicationBasePython/7.4_IO.html#3-raspberry-pi%E2%80%94%E2%80%94gpio
"""

from enum import Enum
from time import sleep

import RPi.GPIO as GPIO

from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD


class PumpStatus(Enum):
    """
    Enum for suction pump status.
    """
    OFF = 1
    ON = 0


def pump_on() -> None:
    """
    Turns on the suction pump.
    """
    GPIO.output(20, PumpStatus.ON.value)
    GPIO.output(21, PumpStatus.ON.value)


def pump_off() -> None:
    """
    Turns off the suction pump.
    """
    GPIO.output(20, PumpStatus.OFF.value)
    sleep(0.05)
    GPIO.output(21, PumpStatus.OFF.value)


def main():
    """
    Main function that uses the pump to lift objects.
    """

    # set GPIO mode
    # Broadcom SOC channel, which refers to the numbering of GPIO pins on a Raspberry Pi
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(channel=20, direction=GPIO.OUT)
    GPIO.setup(channel=21, direction=GPIO.OUT)
    GPIO.output(20, PumpStatus.OFF.value)

    # turn on suction
    GPIO.output(20, PumpStatus.ON.value)
    GPIO.output(21, PumpStatus.ON.value)

    # wait for 5 seconds
    sleep(5)

    # turn off suction
    GPIO.output(20, PumpStatus.OFF.value)
    GPIO.output(21, PumpStatus.OFF.value)


if __name__ == "__main__":
    main()
