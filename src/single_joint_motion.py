#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script controls the joints to form predetermined angles using the pymycobot library.

https://docs.elephantrobotics.com/docs/gitbook-en/7-ApplicationBasePython/7.7_example.html#3--single-joint-motion
"""

import time

from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD
from pymycobot.genre import Angle


def main():
    """
    Main function that controls the joints of a MyCobot to form predetermined angles.
    """
    mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

    # recovery
    mc.send_angles(angles=[0, 0, 0, 0, 0, 0], speed=40)
    time.sleep(1)

    # control joint 3 to move 70°
    mc.send_angle(id=Angle.J3.value, degree=70, speed=40)
    time.sleep(1)

    # control joint 4 movement -70°
    mc.send_angle(id=Angle.J4.value, degree=-70, speed=40)
    time.sleep(1)

    # control joint 1 to move 90°
    mc.send_angle(id=Angle.J1.value, degree=90, speed=40)
    time.sleep(1)

    # control joint 5 movement -90°
    mc.send_angle(id=Angle.J5.value, degree=-90, speed=40)
    time.sleep(1)

    # control joint 5 to move 90°
    mc.send_angle(id=Angle.J5.value, degree=90, speed=40)
    time.sleep(1)


if __name__ == "__main__":
    main()
