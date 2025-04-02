from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD
import time

# Create object code here for Raspberry Pi version
mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

# Check whether the program can be burned into the robot arm
if mc.is_controller_connected() != 1:
    print("Please connect the robot arm correctly for program writing")
    exit(0)

# Set the neutral position
NEUTRAL_POS_COORDS = [-31.7, -51.5, 410.7, -74.87, -3.65, -73.34]
mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=30)

# Release servos to allow manual movement
mc.release_all_servos()

# Choose the file to load
quadrant = input("Enter the quadrant file to load (RF, RB, LF, LB): ")
filename = f"{quadrant}.txt"

# Load recorded angles from the chosen file
try:
    with open(filename, "r") as f:
        positions = [eval(line.strip()) for line in f.readlines()]
    print(f"Loaded {len(positions)} positions from {filename}")

except FileNotFoundError:
    print(f"File {filename} not found. Make sure you recorded this quadrant.")
    exit(1)

# Move to neutral position first
mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=30)
time.sleep(2)

# Replay the recorded motion smoothly
print("Replaying recorded motion smoothly...")
for pos in positions:
    mc.sync_send_angles(pos, 80)  # Faster and smoother motion
    time.sleep(0.05)

print("Motion complete!")

# Release servos again
mc.release_all_servos()
