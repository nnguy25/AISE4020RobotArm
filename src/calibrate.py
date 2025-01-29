#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script calibrates the servos on a MyCobot robot using the pymycobot library.

https://docs.elephantrobotics.com/docs/gitbook-en/7-ApplicationBasePython/7.7_example.html#2-controlling-arms-to-move-them-to-starting-point
"""

import sys

from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD


def main():
    """
    Calibrates the servos on a MyCobot robot.
    """

    mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

    if mc.is_controller_connected() != 1:
        print("Cobot controller is not connected")
        sys.exit(1)

    print("Calibrating the MyCobot robot...")
    print("Printing angles before calibration")
    print(mc.get_angles())

    # Fine-tune the robotic arm to ensure that all the bayonets are aligned in the adjusted position
    mc.send_angles(angles=[0, 0, 0, 0, 0, 0], speed=30)
    # mc.set_gripper_calibration()  # calibrate the gripper

    # Uncomment the following line, manually align cobot and continue calibration
    # mc.release_all_servos()

    for i in range(1, 7, 1):
        mc.set_servo_calibration(i)  # calibrate the servo
        print(f"Servo {i} calibrated")

    print("Printing angles after calibration")
    print(mc.get_angles())


if __name__ == "__main__":
    main()
