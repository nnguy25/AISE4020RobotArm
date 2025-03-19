import cv2
import serial
import json
from ultralytics import YOLO

# Open serial connection to Raspberry Pi (adjust port as needed)
ser = serial.Serial("COM3", 115200, timeout=1)  # Windows example, replace with actual port for Pi

# Load YOLO model
model = YOLO("yolov8n.pt")  # Adjust if using a custom model

# Open camera (USB overhead camera)
cap = cv2.VideoCapture(1)  # Adjust index if needed
if not cap.isOpened():
    print("Error: Could not open the overhead camera")
    exit(1)

print("📷 Running YOLO for fist detection...")

frame_width = int(cap.get(3))  # Get camera width
frame_height = int(cap.get(4))  # Get camera height
mid_x = frame_width // 2  # Middle of the frame (for left/right detection)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Camera frame not captured")
        break

    # Run YOLO object detection on the frame
    results = model(frame)

    # Process detections
    fist_detected = False
    detected_quadrant = None
    fist_center = None  # To store (cx, cy)

    for result in results:
        for box in result.boxes:
            class_id = int(box.cls[0])  # Get class ID
            label = model.names[class_id]  # Get class label

            if label.lower() == "person":  # Treat "Person" as the detected fist
                x1, y1, x2, y2 = map(int, box.xyxy[0])  # Bounding box coordinates
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2  # Find the center of the box
                
                # Determine left or right quadrant
                detected_quadrant = "left" if cx < mid_x else "right"
                fist_center = (cx, cy)  # Save the fist's center coordinates
                fist_detected = True
                break  # Process only the first detected "Person" (fist)

    if fist_detected:
        print(f"👊 Fist detected in {detected_quadrant} quadrant at {fist_center}")

        # Send detected quadrant & middle position to Raspberry Pi
        message = json.dumps({"quadrant": detected_quadrant, "fist_center": fist_center}) + "\n"
        ser.write(message.encode())  # Send as JSON string

    # Show the camera feed
    cv2.imshow("Fist Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break  # Exit loop on 'q' key press

# Release camera
cap.release()
cv2.destroyAllWindows()
ser.close()

ser.write(json.dumps([fist_center,detected_quadrant]).encode('utf-8'))