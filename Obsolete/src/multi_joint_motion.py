#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script moves the joints of a MyCobot robot using the pymycobot library.

https://docs.elephantrobotics.com/docs/gitbook-en/7-ApplicationBasePython/7.7_example.html#4-multi-joint-motion
"""

import time

from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD


def main():
    mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

    # Robotic arm recovery
    mc.send_angles(angles=[0, 0, 0, 0, 0, 0], speed=50)
    time.sleep(2.5)

    # Control different angles of rotation of multiple joints
    mc.send_angles(angles=[90, 45, -90, 90, -90, 90], speed=50)
    time.sleep(2.5)

    # Return the robotic arm to zero
    mc.send_angles(angles=[0, 0, 0, 0, 0, 0], speed=50)
    time.sleep(2.5)

    # Control different angles of rotation of multiple joints
    mc.send_angles(angles=[-90, -45, 90, -90, 90, -90], speed=50)
    time.sleep(2.5)


if __name__ == "__main__":
    main()
