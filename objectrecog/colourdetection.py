import cv2
import numpy as np

def detect_squares_and_rectangles(frame):
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply GaussianBlur to reduce noise and improve edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Apply edge detection with Canny
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for contour in contours:
        # Approximate the contour to reduce the number of points
        approx = cv2.approxPolyDP(contour, 0.04 * cv2.arcLength(contour, True), True)
        
        if len(approx) == 4:  # Check if the shape has 4 corners (square or rectangle)
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            
            # Ensure it's a square or rectangle with a buffer for slight distortions
            if 0.7 <= aspect_ratio <= 1.3:
                cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)
    
    return frame

def main():
    cap = cv2.VideoCapture(1)  # Use rear camera on Surface Pro 7
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        processed_frame = detect_squares_and_rectangles(frame)
        
        cv2.imshow("Detected Squares and Rectangles", processed_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
