from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD
from pymycobot.genre import Coord

from time import sleep
from enum import Enum

import RPi.GPIO as GPIO

import serial
import json

# Create object code here for Raspberry Pi version
mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))

# Check whether the program can be burned into the robot arm
if mc.is_controller_connected() != 1:
    print("Please connect the robot arm correctly for program writing")
    exit(0)

# Replace '/dev/ttyGS0' with the correct serial device on the Pi
ser = serial.Serial('/dev/ttyGS0', 115200, timeout=1)
print("Raspberry Pi is ready to receive messages.")



"""
======Global Variables======
"""
# Positions

NEUTRAL_POS_COORDS = [-51.8, 6.2, 412.8, -79.8, 15.1, -163.28]
READY_POS_COORDS = [-31.7, -51.5, 410.7, -74.87, -3.65, -73.34]
BIN_A_COORDS =[78.5, 42.5, 411.1, -79.88, -0.92, -9.16]
BIN_B_COORDS = [52.7, 7.6, 417.8, -74.6, 25.74, 30.08]
BIN_C_COORDS = [75.6, -88.2, 366.5, -74.4, 7.77, -98.57]
BIN_D_COORDS = [3.4, -65.5, 417.8, -77.34, 0.87, -108.71]
LOADING_ZONE_COORDS = [69.7, -6.7, 379.8, -56.61, -21.41, -42.46]


# Set speed
SPEED = 50


"""
======PUMP action======
"""
class PumpStatus(Enum):
    """
    Enum for suction pump status.
    """
    OFF = 1
    ON = 0
 
def pump_on():
    """
    Turns on the suction pump.
    """
    # GPIO.output(20, PumpStatus.ON.value)  # comment this for strong pump
    GPIO.output(20, PumpStatus.OFF.value)
    GPIO.output(21, PumpStatus.ON.value)

def pump_off():
    """
    Turns off the suction pump, and blows out block.
    """
    GPIO.output(21, PumpStatus.OFF.value)
    GPIO.output(20, PumpStatus.ON.value)
    sleep(0.5)
    #GPIO.output(20, PumpStatus.OFF.value)
    #GPIO.output(20, PumpStatus.ON.value)
    
    #sleep(0.05)
    GPIO.output(20, PumpStatus.OFF.value)



"""
======Movement======
"""
def move_to_bin(bin):

    # Travel to designated bin
    if bin=='A':
        mc.set_color(255,0,0) #red light on
        mc.sync_send_coords(coords=BIN_A_COORDS,speed=SPEED,timeout=3)
    elif bin=='B':
        mc.set_color(255,255,0) #yellow light on
        mc.sync_send_coords(coords=BIN_B_COORDS,speed=SPEED,timeout=3)
    elif bin=='C':
        mc.set_color(0,255,0) #green light on
        mc.sync_send_coords(coords=BIN_C_COORDS,speed=SPEED,timeout=3)
    elif bin=='D':
        mc.set_color(0,0,255) #blue light on
        mc.sync_send_coords(coords=BIN_D_COORDS,speed=SPEED,timeout=3)
    else:
        mc.set_color(255,255,255) #white light on
        mc.sync_send_coords(coords=LOADING_ZONE_COORDS,speed=SPEED,timeout=3)
        
        
def pickup_object(quadrant, name):
    # Choose the file to load
    filename = f"Q{quadrant}.txt"

    # Load recorded angles from the chosen file
    try:
        with open(filename, "r") as f:
            positions = [eval(line.strip()) for line in f.readlines()]
        print(f"Loaded {len(positions)} positions from {filename}")

    except FileNotFoundError:
        print(f"File {filename} not found. Make sure you recorded this quadrant.")
        exit(1)

    # Move to ready position first
    mc.send_coords(coords=READY_POS_COORDS, speed=SPEED)
    sleep(2)

    # Replay the recorded motion smoothly
    print(f"Moving to {name}...")
    for pos in positions:
        mc.sync_send_angles(pos, speed=60)  # Faster and smoother motion
        sleep(0.03)

    print(f"Motion complete! Picking up {name}...")
    
    # Turn pump on to pick up object
    pump_on()
    sleep(2)
    print("Pickup complete!")
    #pr_pos()
    #mc.release_all_servos()
    ready_pos()
    fix_pos()
    ready_pos()
    

def neutral_pos():
    # Return to neutral position
    mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=SPEED)
    #mc.sync_send_coords(coords=NEUTRAL_POS_COORDS,speed=SPEED)
 
 
def ready_pos():
    # Return to ready position
    mc.send_coords(coords=READY_POS_COORDS, speed=SPEED)

def fix_pos():
    # Return to pre-ready position
    mc.send_angle(3, 20, speed=SPEED)
    mc.send_angle(2, -20, speed=SPEED)


"""
======Main function======
"""
def main(categorized_obj):

    # Reset robot arm to neutral position
    print("Resetting robot")
    mc.set_color(128,128,128) #  reset to grey color
    pump_off()
    ready_pos()



    # Receive category
    print("Waiting for Category choice...")
    new_received = received
    while (new_received == received) | (new_received == ''):
            new_received = ser.readline().decode().strip()  # Read incoming data
    chosen_category = new_received.upper()
    # Waits a few seconds to prepare for next input
    print(f"Category '{chosen_category}' received, please wait...")
    ser.write(b"Ready")  # Send acknowledgment
    # Receive bin
    print("Waiting for Bin choice...")
    new_received = received
    while (new_received == received) | (new_received == ''):
            new_received = ser.readline().decode().strip()  # Read incoming data
    chosen_bin= new_received
    print(f"Bin '{chosen_bin}' received.")
    
    # test
    #chosen_category = 'vehicles'.upper()
    #chosen_bin = 'C'
    # Print choices
    print(f'Cleaning up all objects of type "{chosen_category}" to bin "{chosen_bin}"')
    sleep(0.5)

    
    # Iterate through all objects in chosen_category
    for item in categorized_obj[chosen_category]:
        
        # Get object name and quadrant
        name = item[0] #str
        quad = item[1] #int
        print(f"Item '{name}' in quadrant '{quad}'")
        
        # Call function to pick up object
        pickup_object(quad, name)

        # Call function to drop object in bin
        print(f"\nMoving to Bin {chosen_bin}...")
        sleep(1)
        move_to_bin(chosen_bin)
        sleep(1)
        print(f"Releasing {name}...")
        pump_off()
        mc.set_color(128,128,128) #  Reset to grey color
        sleep(1) 
        
        # Return to ready pos for next item
        ready_pos()
    
    
    
    # Fist bump
    ser.write(b"Message received.\n" + received.encode() + b'\n')  # Send acknowledgment
    
    
    
    # Returns to neutral pos when all items of type are exhausted
    print("Returning to base position")
    neutral_pos()

    # End of main(), go back to while loop
    print("Waiting for input...")
    mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=SPEED)







"""
======EXECUTE CODE======
"""


if __name__ == "__main__":
    try:
        # set GPIO mode
        # Broadcom SOC channel, which refers to the numbering of GPIO pins on a Raspberry Pi
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(channel=20, direction=GPIO.OUT)
        GPIO.setup(channel=21, direction=GPIO.OUT)
        # Set Pump to Neutral (pump off, calibrated neutral position)
        pump_off()
        neutral_pos()
        fix_pos()
        neutral_pos()
        
        # Get input from external device
        print("Waiting for input...")
        while True:
            received = ser.readline().decode('utf-8') # Read incoming data
            
            if received:
                print("Received:\n", received)
                # print(type(received))
                categories = json.loads(received)
                #ser.write(b"Message received.\n" + received.encode() + b'\n')  # Send acknowledgment
                
                # run main loop
                main(categories)

                
    
    except KeyboardInterrupt:
        # interrupt through CTRL + C
        # will turn off pump, return to neutral position, then display output message
        print("\nReturning to neutral")
        pump_off()
        neutral_pos()
    finally:
        print("Goodbye!\n== END OF SCRIPT===")
