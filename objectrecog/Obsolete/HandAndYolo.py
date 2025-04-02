import cv2
from ultralytics import YOLO
from collections import Counter
import mediapipe
import threading
import time

import serial
import json

ser = serial.Serial("COM12", 115200, timeout=1)

###Hand Control######################################################

handsModule = mediapipe.solutions.hands
HOLD_THRESHOLD = 15  # Frames a finger must be held up
MULTI_HOLD_THRESHOLD = 10  # Slightly lower threshold for multi-finger actions
choice = None
binChoice = None

# Track how long each finger is raised
finger_counters = {"thumb": 0, "index": 0, "middle": 0, "ring": 0, "pinkie": 0}

watching = False  # Toggle for watching finger inputs

def set_Choice(ch):
    global choice
    choice = ch

def set_BinChoice(ch):
    global binChoice
    binChoice = ch

# Define multi-finger actions
multi_finger_actions = {
    (0, 1, 1, 0, 0): lambda: set_BinChoice("A"),  # Index + Middle
    (0, 1, 1, 1, 0): lambda: set_BinChoice("B"),  # Index + Middle + Ring
    (0, 1, 1, 1, 1): lambda: set_BinChoice("C"),  # No thumb, all others
    (1, 1, 1, 1, 1): lambda: set_BinChoice("D"),  # All fingers
}

# Individual finger actions
finger_actions = {
    "thumb": lambda: set_Choice("Thumb"),
    "index": lambda: set_Choice("FOOD"),
    "middle": lambda: set_Choice("VEHICLES"),
    "ring": lambda: set_Choice("ANIMALS"),
    "pinkie": lambda: set_Choice("OBJECTS"),
}

watching_multi_finger = False  # Toggle for multi-finger recognition mode
multi_finger_triggered = False
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
                multi_finger_actions[fingers_tuple]()  # Send serial message like b"A\n"
                print(f"✅ Triggered Multi-Finger Action: {fingers_tuple}")
                global multi_finger_triggered
                multi_finger_triggered = True  # <- Set flag here
                for i in required_fingers:
                    finger_counters[list(finger_counters.keys())[i]] = 0
                watching_multi_finger = False
                watching = False
        return

    # Otherwise, check individual finger actions
    for i, (finger, action) in enumerate(finger_actions.items()):
        if fingers_state[i] == 1 and finger_counters[finger] >= HOLD_THRESHOLD:
            action()
            print(f"Triggered Individual Action: {finger}")
            finger_counters[finger] = 0
            watching = False


mod=handsModule.Hands()
drawingModule = mediapipe.solutions.drawing_utils

h=480
w=640

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

def findpostion(frame1):
    list=[]
    results = mod.process(cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB))
    if results.multi_hand_landmarks != None:
       for handLandmarks in results.multi_hand_landmarks:
           drawingModule.draw_landmarks(frame1, handLandmarks, handsModule.HAND_CONNECTIONS)
           list=[]
           for id, pt in enumerate (handLandmarks.landmark):
                x = int(pt.x * w)
                y = int(pt.y * h)
                list.append([id,x,y])

    return list            





def findnameoflandmark(frame1):
     list=[]
     results = mod.process(cv2.cvtColor(frame1, cv2.COLOR_BGR2RGB))
     if results.multi_hand_landmarks != None:
        for handLandmarks in results.multi_hand_landmarks:


            for point in handsModule.HandLandmark:
                 list.append(str(point).replace ("< ","").replace("HandLandmark.", "").replace("_"," ").replace("[]",""))
     return list


# Start a background thread to continuously read incoming messages
read_thread = threading.Thread(target=read_from_pi, daemon=True)
read_thread.start()

cap = cv2.VideoCapture(1)          
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
            #print(f"Finger States: {fingers}")

            # Count fingers up and down
            c = Counter(fingers)
            up = c[1]
            down = c[0]
            #print(f"Fingers Up: {up}, Fingers Down: {down}")

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



#### YOLO CODE ####

# Function to get class colors
def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] * (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)

# Function returns objects, grouping, and quadrant
def get_objects():
    # Load the model
    yolo = YOLO('yolov8s.pt')
    # Load the video capture
    videoCap = cv2.VideoCapture(0)

    # CONSTANTS
    CROPPED_W = 300
    CROPPED_H = CROPPED_W
    RESIZE_FACTOR = 3   # increase window size

    # array containing object info
    objects = []

    while True:
        ret, frame = videoCap.read()
        if not ret:
            print("Error: Unable to read video frame")
            break
        # get current frame dims
        h, w, _= frame.shape

        #Calculate center of crop
        x_start = (w - CROPPED_W)//2
        y_start = (h - CROPPED_H)//2
        x_end = x_start + CROPPED_W
        y_end = y_start + CROPPED_H
        

        #Get new frame
        cropped_frame = frame[y_start:y_end, x_start:x_end]

        results = yolo.track(cropped_frame, stream=True)

        # reset objects array
        objects = []
        for result in results:
            # get the classes names
            classes_names = result.names

            # iterate over each box
            for box in result.boxes:
                # check if confidence is greater than 40 percent
                if box.conf[0] > 0.4:
                    # get coordinates
                    [x1, y1, x2, y2] = box.xyxy[0]
                    # convert to int
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                    if((int((x2 + x1)/2) < int(CROPPED_W/2)) & (int((y2 + y1)/2) < int(CROPPED_H/2))):
                        quadrant = 1 #Top Left
                    elif((int((x2 + x1)/2) > int(CROPPED_W/2)) & (int((y2 + y1)/2) < int(CROPPED_H/2))):
                        quadrant = 2 #Top RIght
                    elif((int((x2 + x1)/2) < int(CROPPED_W/2)) & (int((y2 + y1)/2) > int(CROPPED_H/2))):
                        quadrant = 3 #Bottom Left
                    elif((int((x2 + x1)/2) > int(CROPPED_W/2)) & (int((y2 + y1)/2) > int(CROPPED_H/2))):
                        quadrant = 4 #Bottom Right

                    # get the class
                    cls = int(box.cls[0])

                    # get the class name
                    class_name = classes_names[cls]

                    # get the respective colour
                    colour = getColours(cls)

                    # draw the rectangle
                    cv2.rectangle(cropped_frame, (x1, y1), (x2, y2), colour, 2)
                    #cv2.rectangle(cropped_frame, (0, 0))

                    # object info
                    objects.append([class_name, quadrant])

                    # put the class name and confidence on the image
                    cv2.putText(cropped_frame, f'{classes_names[int(box.cls[0])]} {box.conf[0]:.2f} {quadrant}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)
                    
        # show the image
        im = cv2.resize(cropped_frame, (CROPPED_W*RESIZE_FACTOR, CROPPED_H*RESIZE_FACTOR))
        cv2.imshow('frame', im)

        # break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # release the video capture and destroy all windows before returning
            videoCap.release()
            cv2.destroyAllWindows()
            return objects

# categorize each object
def yolo_model():
    # use yolo to get model
    objects = get_objects()

    # get categories
    OBJECT_GROUPS = {'ANIMALS': ['cat', 'cow', 'sheep', 'zebra'],
                 'FOOD': ['orange', 'apple', 'banana', 'carrot', 'pizza'],
                 'VEHICLES': ['motorcycle', 'airplane', 'car', 'bicycle'],
                 'OBJECTS': ['clock', 'remote', 'scissors', 'mouse', 'keyboard', 'book']}
    # copy all dictionary keys
    categories = {key: [] for key in OBJECT_GROUPS}
    # using the keys and values from full object dictionary
    for key, value in OBJECT_GROUPS.items():
        # checks every object
        for item in objects:
            # categorizes each object
            if item[0] in value:
                categories[key] += [item]

    ser.write(json.dumps(categories).encode('utf-8'))
    userInput(categories)


                
def userInput(cat):
    print(cat)
    print("Use your hand to choose which category to pick up.")
    print("Index for Food, Middle for Vehicles, Ring for Animals, Pinkie for Objects")

    watching = True

    while watching:
        time.sleep(0.1)


    print(f"Selected: {choice}")

    ser.write(choice.encode())

    #wait for response form robot to tell it which bin
    while True:
        response = ser.readline().decode().strip()
        if response:
            print("Response:", response)
            if response == "Ready":
                print("Use Multiple finger control to choose which bin")
                print ("Index + Middle for Bin A, Index + Middle + Ring for Bin B, Index + Middle + Ring + Pinkie for Bin C, All fingers for Bin D")
                break
            else:
                print("Waiting for 'Ready'...")
    
    multi_finger_actions = True
    
    while multi_finger_actions:
        time.sleep(0.1)

    print(f"Selected Bin: {binChoice}")
    ser.write(binChoice.encode())

    print("Enjoy the show")

    return



###Running the code######################################################
# run code
if __name__ == "__main__":
    while True:

        yolo_model()

