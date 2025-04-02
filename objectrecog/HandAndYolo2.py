import cv2
from ultralytics import YOLO
import mediapipe
import time
import serial
import json

# Serial connection
ser = serial.Serial("COM14", 115200, timeout=1)

# Mediapipe setup
handsModule = mediapipe.solutions.hands
mod = handsModule.Hands()
drawingModule = mediapipe.solutions.drawing_utils

# Thresholds
HOLD_THRESHOLD = 75

# State tracking
choice = None
binChoice = None

# Fingers being tracked
finger_counters = {
    "index": 0,
    "middle": 0,
    "ring": 0,
    "pinkie": 0
}

# Actions for category selection
finger_actions = {
    "index": lambda: set_Choice("FOOD"),
    "middle": lambda: set_Choice("VEHICLES"),
    "ring": lambda: set_Choice("ANIMALS"),
    "pinkie": lambda: set_Choice("OBJECTS")
}

# Action handlers
def set_Choice(ch):
    global choice
    choice = ch

def set_BinChoice(ch):
    global binChoice
    binChoice = ch

# Hand tracking loop
def hand_input_loop(callback):
    cap = cv2.VideoCapture(0)
    tip = [8, 12, 16, 20]
       # Reset counters at the beginning of each loop
    for k in finger_counters:
        finger_counters[k] = 0

    with handsModule.Hands(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1) as hands:
        watching = True
        while watching:
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

                    for idx, name in enumerate(["index", "middle", "ring", "pinkie"]):
                        tip_id = tip[idx]
                        pip_id = tip_id - 2
                        if a[tip_id][2] < a[pip_id][2]:
                            finger_counters[name] += 1
                            fingers.append(1)
                        else:
                            finger_counters[name] = 0
                            fingers.append(0)

                    raised_fingers = [f for f in finger_counters if finger_counters[f] >= HOLD_THRESHOLD]

                    if len(raised_fingers) == 1:
                        finger = raised_fingers[0]
                        print(f"✅ Detected (held): {finger}")
                        callback(finger)
                        watching = False

            cv2.imshow("Hand Tracking", frame1)
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break

    cap.release()
    cv2.destroyAllWindows()

# YOLO Object detection
def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] * (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)

def get_objects():
    yolo = YOLO('yolov8s.pt')
    videoCap = cv2.VideoCapture(1)

    while True:
        detected_objects = []

        while True:
            ret, frame = videoCap.read()
            if not ret:
                continue

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

            detected_objects = objects
            im = cv2.resize(cropped_frame, (300*3, 300*3))
            cv2.imshow('Object Detection', im)

            key = cv2.waitKey(1)
            if key & 0xFF == ord(' '):
                if not detected_objects:
                    print("❌ No objects detected. Waiting for another attempt...")
                    continue
                print("✅ Space pressed - sending object list to robot.")
                videoCap.release()
                cv2.destroyAllWindows()
                return detected_objects
            elif key & 0xFF == ord('q'):
                print("❌ Quitting object detection.")
                videoCap.release()
                cv2.destroyAllWindows()
                return []

def userInput(categories):
    print(categories)

    # Show category-to-finger mapping
    print("Raise a finger to choose a category:")
    print(" - Index  : FOOD")
    print(" - Middle : VEHICLES")
    print(" - Ring   : ANIMALS")
    print(" - Pinkie : OBJECTS")

    hand_input_loop(lambda finger: finger_actions[finger]())
    print(f"Selected: {choice}")
    ser.write(choice.encode())

    # Show bin-to-finger mapping
    print("📦 Raise a finger to choose a bin:")
    print(" - Index  : A")
    print(" - Middle : B")
    print(" - Ring   : C")
    print(" - Pinkie : D")

    bin_actions = {
        "index": lambda: set_BinChoice("A"),
        "middle": lambda: set_BinChoice("B"),
        "ring": lambda: set_BinChoice("C"),
        "pinkie": lambda: set_BinChoice("D")
    }
    hand_input_loop(lambda finger: bin_actions[finger]())
    print(f"Selected Bin: {binChoice}")
    ser.write(binChoice.encode())
    print("✅ All set! Enjoy the show.")

if __name__ == "__main__":
    while True:
        choice = None
        binChoice = None

        OBJECT_GROUPS = {
        'ANIMALS': ['cat', 'cow', 'sheep', 'zebra'],
        'FOOD': ['orange', 'apple', 'banana', 'carrot', 'pizza'],
        'VEHICLES': ['motorcycle', 'airplane', 'car', 'bicycle'],
        'OBJECTS': ['clock', 'remote', 'scissors', 'mouse', 'keyboard', 'book']
    }

        detected_objects = []
        categories = {}

        while not any(categories.values()):
            detected_objects = get_objects()
            categories = {key: [] for key in OBJECT_GROUPS}
            for key, items in OBJECT_GROUPS.items():
                for obj in detected_objects:
                    if obj[0] in items:
                        categories[key].append(obj)

            if not any(categories.values()):
                print("❌ No categorized objects matched known types. Restarting detection...")
        

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
        userInput(categories)

        print("\n🔄 Cycle complete! Restarting in 2 seconds...\n")
        time.sleep(2)
