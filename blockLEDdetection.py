import cv2
import numpy as np

def detect_blocks():
    cap = cv2.VideoCapture(2)  # Open the camera
    largest_square = None      # Variable to store the largest square
    largest_area = 0           # Variable to store the area of the largest square
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest square only once
        if largest_square is None:
            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(approx) == 4:  # Check if the contour is a quadrilateral (square)
                    area = cv2.contourArea(contour)
                    
                    if area > largest_area:
                        largest_area = area
                        largest_square = approx
        
        # If we found a square, restrict the region to that square
        if largest_square is not None:
            x, y, w, h = cv2.boundingRect(largest_square)
            roi = hsv[y:y+h, x:x+w]  # ROI within the largest square
            
            # Detect blocks only within the largest square
            for contour in contours:
                epsilon = 0.02 * cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                if len(approx) >= 4:  # Assuming blocks are quadrilateral
                    rect_x, rect_y, rect_w, rect_h = cv2.boundingRect(approx)
                    
                    # Check if the block is within the largest square
                    if x <= rect_x <= x + w and y <= rect_y <= y + h:
                        block_roi = roi[rect_y - y:rect_y - y + rect_h, rect_x - x:rect_x - x + rect_w]
                        
                        avg_color = np.mean(block_roi, axis=(0, 1))
                        color_name = classify_color(avg_color)
                        
                        cv2.rectangle(frame, (rect_x, rect_y), (rect_x + rect_w, rect_y + rect_h), (0, 255, 0), 2)
                        cv2.putText(frame, color_name, (rect_x, rect_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        cv2.imshow('Detected Blocks', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

def classify_color(hsv_color):
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

# Start live detection
detect_blocks()
