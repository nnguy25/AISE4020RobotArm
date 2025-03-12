import cv2
import numpy as np

def detect_squares_with_color(frame):
    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Apply histogram equalization to normalize brightness
    equalized = cv2.equalizeHist(gray)
    
    # Apply GaussianBlur to reduce noise and improve edge detection
    blurred = cv2.GaussianBlur(equalized, (5, 5), 0)
    
    # Apply adaptive thresholding to improve edge detection
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    
    # Find contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_squares = []
    
    for contour in contours:
        if cv2.contourArea(contour) < 500:  # Filter out small noise
            continue
        
        # Approximate the contour to reduce the number of points
        approx = cv2.approxPolyDP(contour, 0.02 * cv2.arcLength(contour, True), True)
        
        if len(approx) == 4:  # Check if the shape has 4 corners (square or rectangle)
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            
            # Ensure it's a square with a buffer for slight distortions
            if 0.8 <= aspect_ratio <= 1.2:
                detected_squares.append((approx, x, y, w, h))
                
    for approx, x, y, w, h in detected_squares:
        cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)
        
        # Extract the ROI (Region of Interest) to determine color
        roi = frame[y:y+h, x:x+w]
        avg_color = np.mean(roi, axis=(0, 1))  # Compute average color
        color_name = classify_color(avg_color)  # Classify color
        
        # Display the color name on the square
        cv2.putText(frame, color_name, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    return frame

def classify_color(avg_color):
    # Simple color classification based on RGB values
    b, g, r = avg_color
    if r > 150 and g < 100 and b < 100:
        return "Red"
    elif g > 150 and r < 100 and b < 100:
        return "Green"
    elif b > 150 and r < 100 and g < 100:
        return "Blue"
    elif r > 150 and g > 150 and b < 100:  
        return "Yellow"
    elif r > 200 and g > 200 and b > 200:
        return "White"
    elif r < 50 and g < 50 and b < 50:
        return "Black"
    else:
        return "Unknown"

def main():
    cap = cv2.VideoCapture(0)  # Use front camera on Surface Pro 7
    cap = cv2.VideoCapture(1)  # Use rear camera on Surface Pro 7
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break
        
        processed_frame = detect_squares_with_color(frame)
        
        cv2.imshow("Detected Squares with Color", processed_frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
