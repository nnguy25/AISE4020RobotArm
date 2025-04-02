import cv2
import torch
from ultralytics import YOLO

# Load YOLOv8 model
model = YOLO("yolov8n.pt")  # Using the pretrained YOLOv8 nano model

# Camera setup
cap = cv2.VideoCapture(1)

# Define the hardcoded bounding box (x, y, width, height)
box_x, box_y, box_w, box_h = 150, 100, 300, 300  # Modify as needed

# Define object categories
categories = {
    "food": ["banana", "apple", "pizza", "carrot"],
    "vehicles": ["bicycle", "car", "motorcycle", "airplane"],
    "animals": ["cat", "sheep", "cow", "zebra"],
    "objects": ["mouse", "remote", "clock", "scissors"]
}

def classify_object(label):
    for category, items in categories.items():
        if label in items:
            return category
    return "unknown"

def get_quadrant(cx, cy, box_x, box_y, box_w, box_h):
    mid_x, mid_y = box_x + box_w // 2, box_y + box_h // 2
    if cx < mid_x and cy < mid_y:
        return "Quadrant 1"
    elif cx >= mid_x and cy < mid_y:
        return "Quadrant 2"
    elif cx < mid_x and cy >= mid_y:
        return "Quadrant 3"
    else:
        return "Quadrant 4"

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run YOLOv8 object detection
    results = model(frame)
    
    # Draw the bounding box
    cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 0, 0), 2)
    
    # Process detected objects
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
            conf = float(box.conf[0])  # Confidence score
            class_id = int(box.cls[0])  # Class ID
            label = model.names[class_id].lower()  # Get object name
            
            category = classify_object(label)
            
            if conf > 0.5:  # Confidence threshold
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                
                # Check if object is inside the hardcoded box
                if box_x <= cx <= box_x + box_w and box_y <= cy <= box_y + box_h:
                    quadrant = get_quadrant(cx, cy, box_x, box_y, box_w, box_h)
                    
                    # Display category and quadrant info
                    cv2.putText(frame, f"{label} ({category}, {quadrant})", (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                    
                    # Draw rectangle and center point
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                    
                    print(f"{label.capitalize()} detected as {category} at: ({cx}, {cy}) in {quadrant}")
    
    # Display the result
    cv2.imshow("Frame", frame)
    
    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()