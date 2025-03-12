import cv2
from ultralytics import YOLO

# Load the model
yolo = YOLO('yolov8s.pt')

# Load the video capture
videoCap = cv2.VideoCapture(1)

# Function to get class colors
def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] * (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)

cropped_w = 300
cropped_h = cropped_w

while True:
    ret, frame = videoCap.read()
    if not ret:
        print("Error: Unable to read video frame")
        break
    # get current frame dims
    h, w, _= frame.shape

    #Calculate center of crop
    x_start = (w - cropped_w)//2
    y_start = (h - cropped_h)//2
    x_end = x_start + cropped_w
    y_end = y_start + cropped_h
    

    #Get new frame
    cropped_frame = frame[y_start:y_end, x_start:x_end]

    results = yolo.track(cropped_frame, stream=True)

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

                if((int((x2 + x1)/2) < int(cropped_w/2)) & (int((y2 + y1)/2) < int(cropped_h/2))):
                    quadrant = 1 #Top Left
                elif((int((x2 + x1)/2) > int(cropped_w/2)) & (int((y2 + y1)/2) < int(cropped_h/2))):
                    quadrant = 2 #Top RIght
                elif((int((x2 + x1)/2) < int(cropped_w/2)) & (int((y2 + y1)/2) > int(cropped_h/2))):
                    quadrant = 3 #Bottom Left
                elif((int((x2 + x1)/2) > int(cropped_w/2)) & (int((y2 + y1)/2) > int(cropped_h/2))):
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

                # put the class name and confidence on the image
                cv2.putText(cropped_frame, f'{classes_names[int(box.cls[0])]} {box.conf[0]:.2f} {quadrant}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)
                
    # show the image
    resize_factor = 3
    im = cv2.resize(cropped_frame, (cropped_w*resize_factor, cropped_h*resize_factor))
    cv2.imshow('frame', im)

    # break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release the video capture and destroy all windows
videoCap.release()
cv2.destroyAllWindows()

