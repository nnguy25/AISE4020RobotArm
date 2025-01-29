import cv2
from collections import Counter
from module import findnameoflandmark, findpostion, speak
from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD


mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

def thumb_action():
    print("Thumb function called")
    mc.set_color(0, 0, 255)

def index_action():
    print("Index function called")
    mc.set_color(0, 255, 0)

def middle_action():
    print("Middle function called")
    mc.set_color(255, 0, 0)

def ring_action():
    print("Ring function called")
    mc.set_color(100, 100, 100)

def pinkie_action():
    print("Pinkie function called")
    mc.set_color(255, 255, 255)

cap = cv2.VideoCapture(0)
tip = [8, 12, 16, 20]  # Index, Middle, Ring, Pinkie tip landmarks
fingers = []
finger = []

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to read frame")
        break

    frame1 = cv2.resize(frame, (640, 480))

    a = findpostion(frame1)
    b = findnameoflandmark(frame1)

    if len(b) > 0 and len(a) > 0:
        finger = []

        # Thumb detection
        if a[0][1:] < a[4][1:]:
            finger.append(1)
            print(b[4])
            thumb_action()
        else:
            finger.append(0)

        # Other fingers detection
        fingers = []
        for id in range(0, 4):
            if a[tip[id]][2:] < a[tip[id] - 2][2:]:
                print(b[tip[id]])

                if id == 0:
                    index_action()
                elif id == 1:
                    middle_action()
                elif id == 2:
                    ring_action()
                elif id == 3:
                    pinkie_action()

                fingers.append(1)
            else:
                fingers.append(0)

    x = fingers + finger
    c = Counter(x)
    up = c[1]
    down = c[0]
    print(f"Fingers Up: {up}, Fingers Down: {down}")

    cv2.imshow("Frame", frame1)
    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):
        speak(f"Sir, you have {up} fingers up and {down} fingers down.")
    
    if key == ord("s"):
        break

cap.release()
cv2.destroyAllWindows()
