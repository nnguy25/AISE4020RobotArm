#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD


def main():
    mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

    # Check whether the program can be burned into the robot arm
    if mc.is_controller_connected() != 1:
        print("Cobot controller is not connected")
        exit(1)

    print(f"system version: {mc.get_system_version()}")
    print(f"system power: {mc.is_power_on()}")
    print(f"servo power: {mc.focus_all_servos()}")

    match mc.is_moving():
        case 1:
            print("Moving")
        case 0:
            print("Not moving")
        case -1:
            print("Error")


if __name__ == "__main__":
    main()
