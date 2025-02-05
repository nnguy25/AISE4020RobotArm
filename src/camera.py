#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This script checks the camera connected to the MyCobot.

Press 'q' to quit the camera window.
"""


import cv2


def check_camera():
    """
    Shows the image frame captured by the camera until user hits 'q' to quit.
    """
    cap: cv2.VideoCapture = cv2.VideoCapture(index=0)

    while cv2.waitKey(1) != ord("q"):
        _, frame = cap.read()

        # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        cv2.imshow('frame', frame)

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    check_camera()
