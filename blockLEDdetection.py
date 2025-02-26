import cv2
import numpy as np

# Global variables for storing mouse click coordinates
clicks = []
num_blocks = 0  # User-defined number of blocks to detect

def mouse_callback(event, x, y, flags, param):
    global clicks
    if event == cv2.EVENT_LBUTTONDOWN:
        # Append the coordinates of the click to the clicks list
        if len(clicks) < 4:
            clicks.append((x, y))
        print(f"Click {len(clicks)}: ({x}, {y})")  # Print the coordinates for feedback

def classify_color(hsv_color):
    """Classify the color based on the HSV value"""
    h, s, v = hsv_color
    
    if 10 < h < 25:
        return "Yellow"
    elif 25 < h < 60:
        return "Green"
    elif 90 < h < 130:
        return "Blue"
    elif 0 < h < 10 or 170 < h < 180:
        return "Red"
    else:
        return "Unknown"

def detect_blocks():
    global num_blocks
    cap = cv2.VideoCapture(2)  # Open the camera
    
    # Initialize the window and set up mouse callback
    cv2.imshow('Detected Blocks', np.zeros((480, 640, 3), dtype=np.uint8))  # Display a dummy frame to initialize the window
    cv2.setMouseCallback('Detected Blocks', mouse_callback)

    # Ask the user for the number of blocks they want to detect
    num_blocks = int(input("Enter the number of blocks you want to detect: "))

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # If 4 points have been clicked, define the ROI
        if len(clicks) == 4:
            x1, y1 = clicks[0]  # Top-left
            x2, y2 = clicks[1]  # Top-right
            x3, y3 = clicks[2]  # Bottom-left
            x4, y4 = clicks[3]  # Bottom-right
            
            # Get the bounding box of the ROI (min/max x and y coordinates)
            min_x = min(x1, x2, x3, x4)
            max_x = max(x1, x2, x3, x4)
            min_y = min(y1, y2, y3, y4)
            max_y = max(y1, y2, y3, y4)

            # Crop the frame to the region inside the box
            cropped_frame = frame[min_y:max_y, min_x:max_x]

            # Process the cropped frame (detect contours only inside the box)
            hsv = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 50, 150)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Sort contours by area in descending order
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            # Skip the largest contour, and process the next `num_blocks` contours
            for i, contour in enumerate(contours[0:num_blocks + 1]):  # Skip the first (largest) contour
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)

                if len(approx) >= 4:  # Assuming blocks are quadrilateral
                    rect_x, rect_y, rect_w, rect_h = cv2.boundingRect(approx)

                    # Ensure the contour is inside the selected region
                    if rect_x + min_x >= min_x and rect_y + min_y >= min_y and rect_x + rect_w + min_x <= max_x and rect_y + rect_h + min_y <= max_y:
                        # Crop the block area from the frame to calculate its color
                        block_roi = cropped_frame[rect_y:rect_y+rect_h, rect_x:rect_x+rect_w]

                        # Calculate the average color in the block's region
                        avg_color = np.mean(block_roi, axis=(0, 1))

                        # Convert the average color from BGR to HSV
                        avg_hsv = cv2.cvtColor(np.uint8([[avg_color]]), cv2.COLOR_BGR2HSV)[0][0]
                        color_name = classify_color(avg_hsv)

                        # Draw the rectangle on the original frame and show the color name
                        cv2.rectangle(frame, (rect_x + min_x, rect_y + min_y), 
                                      (rect_x + min_x + rect_w, rect_y + min_y + rect_h), 
                                      (0, 255, 0), 2)
                        cv2.putText(frame, color_name, 
                                    (rect_x + min_x, rect_y + min_y - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, 
                                    (0, 255, 0), 2)

        # Show the frame with the rectangle and the color classification
        cv2.imshow('Detected Blocks', frame)
        
        # Check if the user has pressed 'q' to quit the program
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

# Start live detection
detect_blocks()
