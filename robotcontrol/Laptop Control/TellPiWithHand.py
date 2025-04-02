import cv2
from collections import Counter
from module import findnameoflandmark, findpostion, speak
import mediapipe
import serial
import threading

handsModule = mediapipe.solutions.hands
ser = serial.Serial('COM9', 115200, timeout=1)  # Replace 'COM9' with the correct port

HOLD_THRESHOLD = 15  # Frames the finger must be held up

# Track how long each finger is raised
finger_counters = {"thumb": 0, "index": 0, "middle": 0, "ring": 0, "pinkie": 0}

watching = False  # Toggle for watching finger inputs

def trigger_action(finger_name, action_func):
    """Triggers an action only if the finger is held up for HOLD_THRESHOLD frames."""
    global watching, finger_counters
    if finger_counters[finger_name] >= HOLD_THRESHOLD:
        action_func()
        finger_counters[finger_name] = 0  # Reset counter after action is triggered
        watching = False  # Stop watching after action
        print("Action triggered, stopped watching.")

def thumb_action():
    print("Thumb function called")
    ser.write(b"load\n")

def index_action():
    print("Index function called")
    ser.write(b"A\n")

def middle_action():
    print("Middle function called")
    ser.write(b"B\n")

def ring_action():
    print("Ring function called")
    ser.write(b"C\n")

def pinkie_action():
    print("Pinkie function called")
    ser.write(b"D\n")

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
            fingers = []  # Ensure fingers list is initialized
            
            # Thumb detection (compared against wrist or base landmark)
            if a[4][1] < a[3][1]:  # Thumb tip is to the left of its base (for right hand)
                finger_counters["thumb"] += 1
                trigger_action("thumb", thumb_action)
                fingers.append(1)
            else:
                finger_counters["thumb"] = 0
                fingers.append(0)

            # Other fingers detection
            for id, (finger_name, action_func) in enumerate(
                [("index", index_action), ("middle", middle_action), ("ring", ring_action), ("pinkie", pinkie_action)]
            ):
                tip_id = tip[id]  # Get the tip landmark index
                pip_id = tip_id - 2  # Get the PIP (middle joint) landmark index

                if a[tip_id][2] < a[pip_id][2]:  # Tip is higher than middle joint (finger is up)
                    finger_counters[finger_name] += 1
                    trigger_action(finger_name, action_func)
                    fingers.append(1)
                else:
                    finger_counters[finger_name] = 0
                    fingers.append(0)

            # Debugging: Print which fingers are up
            print(f"Finger States: {fingers}")  # Check if detection works

            # Count fingers up and down
            c = Counter(fingers)
            up = c[1]
            down = c[0]
            print(f"Fingers Up: {up}, Fingers Down: {down}")

        # Show frame
        cv2.imshow("Frame", frame1)

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            speak(f"Sir, you have {up} fingers up and {down} fingers down.")

        if key == ord("s"):  # Stop program
            break

        if key == 32:  # Spacebar toggles watching mode
            watching = not watching
            print("Watching started." if watching else "Watching stopped.")

    cap.release()
    cv2.destroyAllWindows()
