from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD
import time

# Replace with your serial port (e.g., /dev/ttyUSB0 or COM3 on Windows)
mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

# Enable free mode to move the robot manually
mc.set_free_mode(1)
print("Move the robot manually to trace the path...")

positions = []
NEUTRAL_POS_COORDS = [-31.7, -51.5, 410.7, -74.87, -3.65, -73.34]
mc.send_angles(NEUTRAL_POS_COORDS, 50)  # 50% speed

time.sleep(10)

#make it wait to start until input

input("Press Enter to start recording...")

try:
    while True:
        # Read and store the current joint angles
        joints = mc.get_angles()
        print("Current angles:", joints)
        positions.append(joints)
        time.sleep(0.2)

except KeyboardInterrupt:
    print("Recording stopped.")
    mc.set_free_mode(0)  # Disable free mode
    #move to the initial position

    mc.send_angles(NEUTRAL_POS_COORDS, 50)  # 50% speed
    


time.sleep(10)
print("Replaying recorded motion...")

for pos in positions:
    mc.send_angles(pos, 50)  # 50% speed
    time.sleep(0.2)

print("Motion complete!")
mc.release_all_servos()   
