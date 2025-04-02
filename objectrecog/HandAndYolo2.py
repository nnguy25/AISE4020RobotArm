import cv2
from ultralytics import YOLO
import mediapipe
import time
import serial
import json

# Serial connection
ser = serial.Serial("COM12", 115200, timeout=1)

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

    # ADJUST THE CAMERA NUMBER AS NEEDED
    cap = cv2.VideoCapture(1)

    # Landmarks indicies for fingertips
    tip = [8, 12, 16, 20]
    
    # Reset counters at the beginning of each loop
    for k in finger_counters:
        finger_counters[k] = 0

    # Initialize the MediaPipe Hands module, NOTE* change the number of hands as needed
    with handsModule.Hands(static_image_mode=False, min_detection_confidence=0.7, min_tracking_confidence=0.7, max_num_hands=1) as hands:

        # Variable for the while loop
        watching = True
        while watching:
            ret, frame = cap.read()
            if not ret:
                continue

            # Resize the frame for consistency across runs
            frame1 = cv2.resize(frame, (640, 480))
            results = hands.process(cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB))

            # This if statement gets called when it detects a hand in the frame
            if results.multi_hand_landmarks:

                # Draw the lines on the hand to show it is tracking properly
                for handLandmarks in results.multi_hand_landmarks:
                    drawingModule.draw_landmarks(frame1, handLandmarks, handsModule.HAND_CONNECTIONS)

                    # Location to store the hand landmark positions
                    a = []
                    for id, pt in enumerate(handLandmarks.landmark):
                        x = int(pt.x * 640)
                        y = int(pt.y * 480)
                        a.append([id, x, y])

                    # List to store the hand landmark positions
                    fingers = []

                    # Loop through the 4 fingers, grabbing the landmarks
                    for idx, name in enumerate(["index", "middle", "ring", "pinkie"]):
                        tip_id = tip[idx]
                        pip_id = tip_id - 2

                        # Check if the fingertip is above the joint (aka the finger is up relative to the joints)
                        if a[tip_id][2] < a[pip_id][2]:
                            finger_counters[name] += 1
                            fingers.append(1) # Mark finger as raised
                        else:
                            finger_counters[name] = 0
                            fingers.append(0)

                    # Check which fingers have been held up for a long enough duration to avoid immediately grabbing the wrong finger
                    raised_fingers = [f for f in finger_counters if finger_counters[f] >= HOLD_THRESHOLD]

                    # Condition to make sure it only looks for one finger
                    if len(raised_fingers) == 1:
                        # Get the name of the finger that was raised
                        finger = raised_fingers[0]
                        print(f"✅ Detected (held): {finger}")
                        # Call the callback function with the detected finger and exit the loop
                        callback(finger)
                        watching = False

            # Allows the user to view the frame live
            cv2.imshow("Hand Tracking", frame1)

            # Break the loop if the 's' key is pressed (ctrl+c probably works too)
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break

    # Release the webcam and close all OpenCV windows
    cap.release()
    cv2.destroyAllWindows()

# YOLO Object detection
def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] * (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)

# Function to perform real-time object detection using YOLO
def get_objects():
    # Load the model
    yolo = YOLO('yolov8s.pt')

    # ADJUST THE CAMERA NUMBER AS NEEDED
    videoCap = cv2.VideoCapture(0)

    while True:
        # List to store the detected objects
        detected_objects = []

        while True: 
            # Take a snapshot of the camera view
            ret, frame = videoCap.read()
            if not ret:
                continue # Skip if the snapshot did not work

            # Crop a region at the center of the frame
            h, w, _ = frame.shape
            x_start = (w - 300)//2
            y_start = (h - 300)//2
            cropped_frame = frame[y_start:y_start+300, x_start:x_start+300]

            # Run the detection on the snapshot
            results = yolo.track(cropped_frame, stream=True)

            # List to store which objects were detected
            objects = []

            for result in results:
                for box in result.boxes:

                    # Looking at the objects, only grab the ones that are above 40% confidence
                    if box.conf[0] > 0.4:
                        # Determine the center of the image to then decide what the quadrants are
                        [x1, y1, x2, y2] = map(int, box.xyxy[0])
                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2

                        # Label and define the quadrants
                        quadrant = 1 if cx < 150 and cy < 150 else 2 if cx >= 150 and cy < 150 else 3 if cx < 150 else 4

                        # Get the object class ID, name, and assign it a colour based on the class
                        cls = int(box.cls[0])
                        name = result.names[cls]
                        colour = getColours(cls)

                        # Draw a rectangle around the objects that are detected, and show the name and confidence
                        cv2.rectangle(cropped_frame, (x1, y1), (x2, y2), colour, 2)
                        cv2.putText(cropped_frame, f'{name} {box.conf[0]:.2f} Q{quadrant}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)

                        # Add the object and quadrant to the list
                        objects.append([name, quadrant])

            # Update the list and show the detection output
            detected_objects = objects
            im = cv2.resize(cropped_frame, (300*3, 300*3))
            cv2.imshow('Object Detection', im)

            # Wait for any key to be pressed before it takes the snapshot
            key = cv2.waitKey(1)

            # Condition to make sure that objects are in the frame
            if key & 0xFF == ord(' '):
                if not detected_objects:
                    print("❌ No objects detected. Waiting for another attempt...")
                    continue
                print("✅ Space pressed - sending object list to robot.")
                videoCap.release()
                cv2.destroyAllWindows()
                return detected_objects

            # If 'q' is pressed, exit the detection
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

    # Call the hand tracking and print what it found for category
    hand_input_loop(lambda finger: finger_actions[finger]())
    print(f"Selected: {choice}")
    ser.write(choice.encode())

    # Show bin-to-finger mapping
    print("📦 Raise a finger to choose a bin:")
    print(" - Index  : A")
    print(" - Middle : B")
    print(" - Ring   : C")
    print(" - Pinkie : D")

    # Set up which bin correlates to which finger
    bin_actions = {
        "index": lambda: set_BinChoice("A"),
        "middle": lambda: set_BinChoice("B"),
        "ring": lambda: set_BinChoice("C"),
        "pinkie": lambda: set_BinChoice("D")
    }

    # Call the hand tracking and print what it found for bin
    hand_input_loop(lambda finger: bin_actions[finger]())
    print(f"Selected Bin: {binChoice}")
    ser.write(binChoice.encode())
    print("✅ All set! Enjoy the show.")

if __name__ == "__main__":
    while True:

        # Placeholders for the category and bin
        choice = None
        binChoice = None

        # Dictionary to categorize the detected objects into the groups
        OBJECT_GROUPS = {
        'ANIMALS': ['cat', 'cow', 'sheep', 'zebra'],
        'FOOD': ['orange', 'apple', 'banana', 'carrot', 'pizza'],
        'VEHICLES': ['motorcycle', 'airplane', 'car', 'bicycle'],
        'OBJECTS': ['clock', 'remote', 'scissors', 'mouse', 'keyboard', 'book']
    }

        # List to store objects detected in the scene, dictionary for categorized objects
        detected_objects = []
        categories = {}

        # Continue the object detection until at least one object is in a known category
        while not any(categories.values()):
            # Call function to detect objects
            detected_objects = get_objects()

            # Initiliaze categories with empty lists
            categories = {key: [] for key in OBJECT_GROUPS}

            # Loop throguh each object that is detected and put in the group it relates to
            for key, items in OBJECT_GROUPS.items():
                for obj in detected_objects:
                    if obj[0] in items:
                        categories[key].append(obj)

            # Restart if no objects detected
            if not any(categories.values()):
                print("❌ No categorized objects matched known types. Restarting detection...")
        
        # IS THIS NEEDED? IT IS DEFINED JUST ABOVE
        OBJECT_GROUPS = {
            'ANIMALS': ['cat', 'cow', 'sheep', 'zebra'],
            'FOOD': ['orange', 'apple', 'banana', 'carrot', 'pizza'],
            'VEHICLES': ['motorcycle', 'airplane', 'car', 'bicycle'],
            'OBJECTS': ['clock', 'remote', 'scissors', 'mouse', 'keyboard', 'book']
        }

        # AGAIN IS THIS NEEDED, SHOWN ABOVE
        categories = {key: [] for key in OBJECT_GROUPS}
        for key, items in OBJECT_GROUPS.items():
            for obj in detected_objects:
                if obj[0] in items:
                    categories[key].append(obj)

        # Send categorized objects to a serial connection
        ser.write(json.dumps(categories).encode('utf-8'))
        userInput(categories)

        # Restart the cycle so that it is automatically 
        print("\n🔄 Cycle complete! Restarting in 2 seconds...\n")
        time.sleep(2)
