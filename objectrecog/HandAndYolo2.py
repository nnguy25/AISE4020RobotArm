import cv2
from ultralytics import YOLO
from collections import Counter
import mediapipe
import threading
import time
import serial
import json

# Serial connection
ser = serial.Serial("COM12", 115200, timeout=1)

# Mediapipe setup
handsModule = mediapipe.solutions.hands
mod = handsModule.Hands()
drawingModule = mediapipe.solutions.drawing_utils

# State tracking
HOLD_THRESHOLD = 15
MULTI_HOLD_THRESHOLD = 10
choice = None
binChoice = None
watching = False
watching_multi_finger = False
multi_finger_triggered = False
waiting_for_bin = False

finger_counters = {"thumb": 0, "index": 0, "middle": 0, "ring": 0, "pinkie": 0}

# Action handlers
def set_Choice(ch):
    global choice, watching
    choice = ch
    watching = False

def set_BinChoice(ch):
    global binChoice, waiting_for_bin
    binChoice = ch
    waiting_for_bin = False

multi_finger_actions = {
    (0, 1, 1, 0, 0): lambda: set_BinChoice("A"),
    (0, 1, 1, 1, 0): lambda: set_BinChoice("B"),
    (0, 1, 1, 1, 1): lambda: set_BinChoice("C"),
    (1, 1, 1, 1, 1): lambda: set_BinChoice("D"),
}

finger_actions = {
    "thumb": lambda: set_Choice("Thumb"),
    "index": lambda: set_Choice("FOOD"),
    "middle": lambda: set_Choice("VEHICLES"),
    "ring": lambda: set_Choice("ANIMALS"),
    "pinkie": lambda: set_Choice("OBJECTS"),
}

def trigger_action(fingers_state):
    global watching_multi_finger, finger_counters
    fingers_tuple = tuple(fingers_state)

    print(f"Finger state: {fingers_state}")
    print(f"Finger counters: {finger_counters}")
    print(f"Watching multi-finger: {watching_multi_finger}")
    print(f"Multi-finger triggered: {multi_finger_triggered}")

    if watching_multi_finger:
        print(f"Checking multi-finger: {fingers_tuple}")
        if fingers_tuple in multi_finger_actions:
            required_fingers = [i for i, state in enumerate(fingers_tuple) if state == 1]
            if all(finger_counters[list(finger_counters.keys())[i]] >= MULTI_HOLD_THRESHOLD for i in required_fingers):
                print("✅ Multi-finger action detected!")
                multi_finger_actions[fingers_tuple]()
                for i in required_fingers:
                    finger_counters[list(finger_counters.keys())[i]] = 0
                watching_multi_finger = False
    else:
        # Individual finger input for category
        for i, (finger, action) in enumerate(finger_actions.items()):
            if fingers_state[i] == 1 and finger_counters[finger] >= HOLD_THRESHOLD:
                print(f"Detected individual: {finger}")
                action()
                finger_counters[finger] = 0

# Hand tracking loop (camera 1)
def hand_input_loop():
    global watching, watching_multi_finger
    cap = cv2.VideoCapture(1)
    tip = [8, 12, 16, 20]

    with handsModule.Hands(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1) as hands:
        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            frame1 = cv2.resize(frame, (640, 480))
            results = hands.process(cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB))
            if results.multi_hand_landmarks:
                for handLandmarks in results.multi_hand_landmarks:
                    drawingModule.draw_landmarks(frame1, handLandmarks, handsModule.HAND_CONNECTIONS)
                    a = []
                    for id, pt in enumerate(handLandmarks.landmark):
                        x = int(pt.x * 640)
                        y = int(pt.y * 480)
                        a.append([id, x, y])

                    fingers = []
                    if a[4][1] < a[3][1]:
                        finger_counters["thumb"] += 1
                        fingers.append(1)
                    else:
                        finger_counters["thumb"] = 0
                        fingers.append(0)

                    for idx, name in enumerate(["index", "middle", "ring", "pinkie"]):
                        tip_id = tip[idx]
                        pip_id = tip_id - 2
                        if a[tip_id][2] < a[pip_id][2]:
                            finger_counters[name] += 1
                            fingers.append(1)
                        else:
                            finger_counters[name] = 0
                            fingers.append(0)

                    if watching:
                        trigger_action(fingers)

            cv2.imshow("Hand Tracking", frame1)
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break

    cap.release()
    cv2.destroyAllWindows()

# YOLO object detection (camera 2)
def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] * (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)

def get_objects():
    yolo = YOLO('yolov8s.pt')
    videoCap = cv2.VideoCapture(0)
    while True:
        ret, frame = videoCap.read()
        if not ret:
            break
        h, w, _ = frame.shape
        x_start = (w - 300)//2
        y_start = (h - 300)//2
        cropped_frame = frame[y_start:y_start+300, x_start:x_start+300]
        results = yolo.track(cropped_frame, stream=True)
        objects = []
        for result in results:
            for box in result.boxes:
                if box.conf[0] > 0.4:
                    [x1, y1, x2, y2] = map(int, box.xyxy[0])
                    cx = (x1 + x2) // 2
                    cy = (y1 + y2) // 2
                    quadrant = 1 if cx < 150 and cy < 150 else 2 if cx >= 150 and cy < 150 else 3 if cx < 150 else 4
                    cls = int(box.cls[0])
                    name = result.names[cls]
                    colour = getColours(cls)
                    cv2.rectangle(cropped_frame, (x1, y1), (x2, y2), colour, 2)
                    cv2.putText(cropped_frame, f'{name} {box.conf[0]:.2f} Q{quadrant}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)
                    objects.append([name, quadrant])
        im = cv2.resize(cropped_frame, (300*3, 300*3))
        cv2.imshow('Object Detection', im)
        if cv2.waitKey(1) & 0xFF == ord('q'):
     #       videoCap.release()
      #      cv2.destroyAllWindows()
            return objects
    #videoCap.release()
    #cv2.destroyAllWindows()
    return objects

def yolo_model():
    objects = get_objects()
    if objects is None:
        print("No objects detected.")
        return

    OBJECT_GROUPS = {
        'ANIMALS': ['cat', 'cow', 'sheep', 'zebra'],
        'FOOD': ['orange', 'apple', 'banana', 'carrot', 'pizza'],
        'VEHICLES': ['motorcycle', 'airplane', 'car', 'bicycle'],
        'OBJECTS': ['clock', 'remote', 'scissors', 'mouse', 'keyboard', 'book']
    }
    categories = {key: [] for key in OBJECT_GROUPS}
    for key, items in OBJECT_GROUPS.items():
        for obj in objects:
            if obj[0] in items:
                categories[key].append(obj)

    ser.write(json.dumps(categories).encode('utf-8'))
    userInput(categories)

def userInput(cat):
    global watching, waiting_for_bin, watching_multi_finger
    print(cat)
    print("Use your hand to choose which category to pick up.")
    watching = True  # Now triggers hand loop
    while watching:
        time.sleep(0.1)

    print(f"Selected: {choice}")
    ser.write(choice.encode())

    while True:
        response = ser.readline().decode().strip()
        if response == "Ready":
            print("Use multi-finger gesture to select a bin")
            break

    waiting_for_bin = True
    watching_multi_finger = True  # <-- this was missing!
    while  watching_multi_finger:
        time.sleep(0.1)

    print(f"Selected Bin: {binChoice}")
    ser.write(binChoice.encode())
    print("Enjoy the show")


if __name__ == "__main__":
    # STEP 1: Detect objects first
    detected_objects = get_objects()
    if not detected_objects:
        print("No objects detected.")
        exit()

    # STEP 2: Start hand tracking in parallel
    hand_thread = threading.Thread(target=hand_input_loop, daemon=True)
    hand_thread.start()

    # STEP 3: Continue with classification and hand interaction
    OBJECT_GROUPS = {
        'ANIMALS': ['cat', 'cow', 'sheep', 'zebra'],
        'FOOD': ['orange', 'apple', 'banana', 'carrot', 'pizza'],
        'VEHICLES': ['motorcycle', 'airplane', 'car', 'bicycle'],
        'OBJECTS': ['clock', 'remote', 'scissors', 'mouse', 'keyboard', 'book']
    }
    categories = {key: [] for key in OBJECT_GROUPS}
    for key, items in OBJECT_GROUPS.items():
        for obj in detected_objects:
            if obj[0] in items:
                categories[key].append(obj)

    ser.write(json.dumps(categories).encode('utf-8'))

    # STEP 4: Now wait for hand input
    userInput(categories)
