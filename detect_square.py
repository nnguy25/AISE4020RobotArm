import cv2
import numpy as np

def detect_quadrilaterals():
    cap = cv2.VideoCapture(2)  # Open webcam

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian Blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny Edge Detection
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            # Approximate the shape
            epsilon = 0.02 * cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, epsilon, True)

            # Check if the shape has 4 sides (quadrilateral)
            if len(approx) == 4:
                # Draw the quadrilateral
                cv2.drawContours(frame, [approx], 0, (0, 255, 0), 3)  # Green color
                
                # Extract coordinates of the quadrilateral
                coordinates = [(point[0][0], point[0][1]) for point in approx]

                # Display coordinates on the screen
                for i, (x, y) in enumerate(coordinates):
                    cv2.putText(frame, f"{i+1}: ({x},{y})", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Display the result
        cv2.imshow("Quadrilateral Detection", frame)

        # Exit on 'q' key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    detect_quadrilaterals()
