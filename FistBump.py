import cv2
import torch
from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD
from time import sleep
from ultralytics import YOLO  # Ensure YOLO is installed (`pip install ultralytics`)

# Initialize MyCobot
mc = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))
if mc.is_controller_connected() != 1:
    print("Please connect the robot arm correctly for program execution")
    exit(1)

# Load YOLO model
model = YOLO("yolov8n.pt")  # Change if using a custom model

# Robot positions (adjust as needed)
NEUTRAL_POS_COORDS = [57.5, -64.4, 408.6, -92.37, 0.17, -89.83]  # Neutral position
LEFT_FIST_COORDS  = [142.1, 19.9, 380.7, -85.0, -12.9, -50.92]   # Left quadrant position
RIGHT_FIST_COORDS = [130.2, -52.1, 382.4, -85.64, -8.24, -84.2]  # Right quadrant position
MOVE_SPEED = 30  # Movement speed (0-100)

# Open USB camera (Overhead View)
cap = cv2.VideoCapture(1)  # Adjust index if needed
if not cap.isOpened():
    print("Error: Could not open the overhead camera")
    exit(1)

# Move robot to the neutral position
print("✅ Getting into neutral position")
mc.send_coords(NEUTRAL_POS_COORDS, MOVE_SPEED, 0)  # Move to neutral
sleep(2)

print("📷 Scanning for a fist...")

detected_quadrant = None
frame_width = int(cap.get(3))  # Camera frame width
mid_x = frame_width // 2  # Middle of the frame (used for left/right detection)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Camera frame not captured")
        break

    # Run YOLO object detection on the frame
    results = model(frame)

    # Process detections
    fist_detected = False
    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])  # Get class ID
            label = model.names[class_id]  # Get class label

            if label.lower() == "person":  # Treat "Person" as the detected fist
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Find the center of the box
                
                # Determine left or right quadrant
                if cx < mid_x:
                    detected_quadrant = "left"
                else:
                    detected_quadrant = "right"
                
                fist_detected = True
                break  # We only need one detected "Person" (fist)

    if fist_detected:
        print(f"👊 Fist detected in {detected_quadrant} quadrant")
        break  # Stop detection once we confirm a fist

# Release camera
cap.release()
cv2.destroyAllWindows()

# Move robot toward the detected fist position
if detected_quadrant:
    print("🤖 Moving to fist bump position")
    if detected_quadrant == "left":
        target_coords = LEFT_FIST_COORDS
    else:
        target_coords = RIGHT_FIST_COORDS
    
    mc.send_coords(target_coords, MOVE_SPEED, 0)  # Move to fist bump position
    sleep(2)  # Ensure movement is complete

    print("✅ Fist bump complete! Returning to neutral position.")
    mc.send_coords(NEUTRAL_POS_COORDS, MOVE_SPEED, 0)  # Return to neutral
else:
    print("❌ No fist detected. Staying in neutral position.")
