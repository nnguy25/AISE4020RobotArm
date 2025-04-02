import cv2
from collections import Counter
from module import findnameoflandmark, findpostion, speak
import mediapipe
import serial
import threading

handsModule = mediapipe.solutions.hands
ser = serial.Serial('COM11', 115200, timeout=1)  # Replace 'COM12' with the correct port

HOLD_THRESHOLD = 15  # Frames a finger must be held up
MULTI_HOLD_THRESHOLD = 10  # Slightly lower threshold for multi-finger actions

# Track how long each finger is raised
finger_counters = {"thumb": 0, "index": 0, "middle": 0, "ring": 0, "pinkie": 0}

watching = False  # Toggle for watching finger inputs

# Define multi-finger actions
multi_finger_actions = {
    (0, 1, 1, 0, 0): lambda: ser.write(b"TwoFingers\n"),  # Index + Middle
    (0, 1, 1, 1, 0): lambda: ser.write(b"ThreeFingers\n"),  # Index + Middle + Ring
    (0, 1, 1, 1, 1): lambda: ser.write(b"FourFingers\n"),  # No thumb, all others
    (1, 1, 1, 1, 1): lambda: ser.write(b"ALL\n"),  # All fingers
}

# Individual finger actions
finger_actions = {
    "thumb": lambda: ser.write(b"Thumb\n"),
    "index": lambda: ser.write(b"Food\n"),
    "middle": lambda: ser.write(b"Vehicles\n"),
    "ring": lambda: ser.write(b"Animals\n"),
    "pinkie": lambda: ser.write(b"Objects\n"),
}
import time

watching_multi_finger = False  # Toggle for multi-finger recognition mode
last_toggle_time = 0  # Stores the last time multi-finger mode was toggled
TOGGLE_COOLDOWN = 1  # 1-second cooldown to prevent rapid toggling

def trigger_action(fingers_state):
    """Check for activation gestures, then multi-finger or individual actions."""
    global watching_multi_finger, watching, finger_counters, last_toggle_time

    fingers_tuple = tuple(fingers_state)
    current_time = time.time()

    # Check for Shaka Gesture (Thumb + Pinkie Extended)
    if fingers_tuple == (1, 0, 0, 0, 1) and (current_time - last_toggle_time) > TOGGLE_COOLDOWN:
        watching_multi_finger = not watching_multi_finger  # Toggle mode
        last_toggle_time = current_time  # Update last toggle time

        if watching_multi_finger:
            print("🔵 Multi-Finger Mode Activated 🔵")
            cv2.putText(frame1, "MULTI-FINGER MODE", (200, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            cv2.imshow("Frame", frame1)
            cv2.waitKey(500)  # Short pause for better user feedback
        else:
            print("⚪ Multi-Finger Mode Deactivated ⚪")

        return  # Prevent triggering other actions on this frame

    # If in multi-finger mode, IGNORE individual finger actions
    if watching_multi_finger:
        if fingers_tuple in multi_finger_actions:
            required_fingers = [i for i, state in enumerate(fingers_tuple) if state == 1]
            if all(finger_counters[list(finger_counters.keys())[i]] >= MULTI_HOLD_THRESHOLD for i in required_fingers):
                multi_finger_actions[fingers_tuple]()
                print(f"✅ Triggered Multi-Finger Action: {fingers_tuple}")
                for i in required_fingers:
                    finger_counters[list(finger_counters.keys())[i]] = 0
                watching_multi_finger = False  # Turn off after action
                watching = False
        return  # Exit function so no individual finger actions run

    # Otherwise, check individual finger actions
    for i, (finger, action) in enumerate(finger_actions.items()):
        if fingers_state[i] == 1 and finger_counters[finger] >= HOLD_THRESHOLD:
            action()
            print(f"Triggered Individual Action: {finger}")
            finger_counters[finger] = 0
            watching = False



def read_from_pi():
    """ Continuously read and display messages from the Raspberry Pi """
    while True:
        try:
            response = ser.readline().decode().strip()
            if response:
                print("\nPi:", response)
        except Exception as e:
            print("Error reading:", e)
            break

# Start a background thread to continuously read incoming messages
read_thread = threading.Thread(target=read_from_pi, daemon=True)
read_thread.start()

cap = cv2.VideoCapture(0)
tip = [8, 12, 16, 20]  # Index, Middle, Ring, Pinkie tip landmarks

with handsModule.Hands(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1) as hands:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to read frame")
            break

        frame1 = cv2.resize(frame, (640, 480))

        a = findpostion(frame1)
        b = findnameoflandmark(frame1)

        if watching and len(b) > 0 and len(a) > 0:
            fingers = []  # List for current finger states
            
            # Thumb detection (compared against wrist or base landmark)
            if a[4][1] < a[3][1]:  # Thumb tip is to the left of its base (for right hand)
                finger_counters["thumb"] += 1
                fingers.append(1)
            else:
                finger_counters["thumb"] = 0
                fingers.append(0)

            # Other fingers detection
            for id, (finger_name) in enumerate(["index", "middle", "ring", "pinkie"]):
                tip_id = tip[id]  # Get the tip landmark index
                pip_id = tip_id - 2  # Get the PIP (middle joint) landmark index

                if a[tip_id][2] < a[pip_id][2]:  # Tip is higher than middle joint (finger is up)
                    finger_counters[finger_name] += 1
                    fingers.append(1)
                else:
                    finger_counters[finger_name] = 0
                    fingers.append(0)

            # Debugging: Print which fingers are up
            print(f"Finger States: {fingers}")

            # Count fingers up and down
            c = Counter(fingers)
            up = c[1]
            down = c[0]
            print(f"Fingers Up: {up}, Fingers Down: {down}")

            # Trigger appropriate actions
            trigger_action(fingers)

        # Show frame
        cv2.imshow("Frame", frame1)

        key = cv2.waitKey(1) & 0xFF


        if key == ord("s"):  # Stop program
            break

        if key == 32:  # Spacebar toggles watching mode
            watching = not watching
            print("Watching started." if watching else "Watching stopped.")

        if key == 13:  # Enter key toggles multi-finger mode
            watching_multi_finger = not watching_multi_finger
            if watching_multi_finger:
                print("🔵 Multi-Finger Mode Activated 🔵")
            else:
                print("⚪ Multi-Finger Mode Deactivated ⚪")


    cap.release()
    cv2.destroyAllWindows()
