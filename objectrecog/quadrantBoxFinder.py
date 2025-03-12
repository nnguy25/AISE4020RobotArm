import cv2
import numpy as np

# Camera setup (change index if necessary)
cap = cv2.VideoCapture(1)

# Define the hardcoded bounding box (x, y, width, height)
box_x, box_y, box_w, box_h = 150, 100, 300, 300  # Modify as needed

# Color ranges in HSV for red, blue, yellow, and green
color_ranges = {
    "red": [(np.array([0, 120, 70]), np.array([10, 255, 255])),  # Lower red
            (np.array([170, 120, 70]), np.array([180, 255, 255]))],  # Upper red
    "blue": [(np.array([100, 150, 50]), np.array([140, 255, 255]))],  # Blue
    "yellow": [(np.array([20, 100, 100]), np.array([30, 255, 255]))],  # Yellow
    "green": [(np.array([40, 50, 50]), np.array([90, 255, 255]))]  # Green
}

# Ask for user input to specify which color to detect
selected_color = input("Enter block color to detect (red, blue, yellow, green): ").strip().lower()

if selected_color not in color_ranges:
    print("Invalid color selected. Defaulting to green.")
    selected_color = "green"

# Function to detect the quadrant
def get_quadrant(cx, cy, box_x, box_y, box_w, box_h):
    mid_x, mid_y = box_x + box_w // 2, box_y + box_h // 2
    if cx < mid_x and cy < mid_y:
        return "Upper Left"
    elif cx >= mid_x and cy < mid_y:
        return "Upper Right"
    elif cx < mid_x and cy >= mid_y:
        return "Bottom Left"
    else:
        return "Bottom Right"

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convert frame to HSV for color detection
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Create a mask for the selected color
    mask = np.zeros_like(hsv[:, :, 0])  # Initialize mask as black
    for lower, upper in color_ranges[selected_color]:
        mask |= cv2.inRange(hsv, lower, upper)  # Combine masks if multiple ranges exist (e.g., red)

    # Find contours of detected objects
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw the bounding box
    cv2.rectangle(frame, (box_x, box_y), (box_x + box_w, box_y + box_h), (255, 0, 0), 2)

    # Process detected blocks
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 500:  # Ignore small noise
            x, y, w, h = cv2.boundingRect(contour)
            cx, cy = x + w // 2, y + h // 2

            # Check if block is inside the hardcoded box
            if box_x <= cx <= box_x + box_w and box_y <= cy <= box_y + box_h:
                quadrant = get_quadrant(cx, cy, box_x, box_y, box_w, box_h)
                
                # Display quadrant info
                cv2.putText(frame, quadrant, (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                # Draw rectangle and center point
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)

                # Print the center coordinates of the detected block
                print(f"{selected_color.capitalize()} block detected at: ({cx}, {cy}) in {quadrant}")

    # Display the result
    cv2.imshow("Frame", frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
