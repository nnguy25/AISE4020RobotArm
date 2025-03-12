from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD
import time

# Create object code here for Raspberry Pi version
mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

# Check whether the program can be burned into the robot arm
if mc.is_controller_connected() != 1:
    print("Please connect the robot arm correctly for program writing")
    exit(0)

print("Move the robot manually to trace the path...")

positions = []
NEUTRAL_POS_COORDS = [-31.7, -51.5, 410.7, -74.87, -3.65, -73.34]
mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=30)

mc.release_all_servos()

#make it wait to start until input

name = input("Name File for quadrant:")

input("Press Enter to start recording...")

try:
    while True:
        # Read and store the current joint angles
        joints = mc.get_angles()
        positions.append(joints)
        time.sleep(0.5)

except KeyboardInterrupt:
    print("Recording stopped.")
    mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=30)
    #move to the initial position
    #export to txt file
    with open(name, "w") as f:
        for pos in positions:
            f.write(str(pos) + "\n")
    


time.sleep(5)
print("Replaying recorded motion smoothly...")

for pos in positions:
    mc.sync_send_angles(pos, 80)  # Faster and smoother motion

print("Motion complete!")

mc.release_all_servos()   
