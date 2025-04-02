import cv2
from ultralytics import YOLO


# Function to get class colors
def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] * (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)

# Function returns objects, grouping, and quadrant
def get_objects():

    # CONSTANTS
    CROPPED_W = 300
    CROPPED_H = CROPPED_W
    RESIZE_FACTOR = 3   # increase window size

    # array containing object info
    objects = []

    while True:
        ret, frame = videoCap.read()
        if not ret:
            print("Error: Unable to read video frame")
            break
        # get current frame dims
        h, w, _= frame.shape

        #Calculate center of crop
        x_start = (w - CROPPED_W)//2
        y_start = (h - CROPPED_H)//2
        x_end = x_start + CROPPED_W
        y_end = y_start + CROPPED_H
        

        #Get new frame
        cropped_frame = frame[y_start:y_end, x_start:x_end]

        results = yolo.track(cropped_frame, stream=True)

        # reset objects array
        objects = []
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

                    if((int((x2 + x1)/2) < int(CROPPED_W/2)) & (int((y2 + y1)/2) < int(CROPPED_H/2))):
                        quadrant = 1 #Top Left
                    elif((int((x2 + x1)/2) > int(CROPPED_W/2)) & (int((y2 + y1)/2) < int(CROPPED_H/2))):
                        quadrant = 2 #Top RIght
                    elif((int((x2 + x1)/2) < int(CROPPED_W/2)) & (int((y2 + y1)/2) > int(CROPPED_H/2))):
                        quadrant = 3 #Bottom Left
                    elif((int((x2 + x1)/2) > int(CROPPED_W/2)) & (int((y2 + y1)/2) > int(CROPPED_H/2))):
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

                    # object info
                    objects += [class_name, quadrant]

                    # put the class name and confidence on the image
                    cv2.putText(cropped_frame, f'{classes_names[int(box.cls[0])]} {box.conf[0]:.2f} {quadrant}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)
                    
        # show the image
        im = cv2.resize(cropped_frame, (CROPPED_W*RESIZE_FACTOR, CROPPED_H*RESIZE_FACTOR))
        cv2.imshow('frame', im)

        # break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            # release the video capture and destroy all windows before returning
            videoCap.release()
            cv2.destroyAllWindows()
            return objects

# categorize each object
def categorize_objects(objects):
    OBJECT_GROUPS = {'ANIMALS': ['cat', 'cow', 'sheep', 'zebra'],
                 'FOOD': ['pizza', 'apple', 'banana', 'carrot'],
                 'VEHICLES': ['motorcycle', 'airplane', 'car', 'bicycle'],
                 'OBJECTS': ['clock', 'remote', 'scissors', 'mouse']}
    # copy all dictionary keys
    categories = {key: [] for key in OBJECT_GROUPS}
    # using the keys and values from full object dictionary
    for key, value in OBJECT_GROUPS.items():
        # checks every object
        for item in objects:
            # categorizes each object
            if item[0] in value:
                categories[key] += [item]
    # returns dictionary of categories
    return categories



# run code
if __name__ == "__main__":
    # Load the model
    yolo = YOLO('yolov8s.pt')
    # Load the video capture
    videoCap = cv2.VideoCapture(1)
    # returns class_name and quadrant
    objects = get_objects()
    categories = categorize_objects(objects)


