from pymycobot.mycobot import MyCobot
from pymycobot import PI_PORT, PI_BAUD

from time import sleep
from enum import Enum

import RPi.GPIO as GPIO

import serial

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
NEUTRAL_POS_COORDS = [57.5, -64.4, 408.6, -92.37, 0.17, -89.83]
BIN_A_COORDS = [103.6, 75.2, 402.2, -88.15, 1.71, -24.46]
BIN_B_COORDS = [46.0, 67.6, 407.3, -87.93, 11.96, 18.44]
BIN_C_COORDS = [105.3, -110.7, 349.8, -83.04, 16.89, -112.61]
BIN_D_COORDS = [73.1, -124.9, 393.2, -92.03, 6.24, -124.85]
LOADING_ZONE_COORDS = [119.8, 33.7, 380.3, -81.99, 3.74, -43.88]
# Set speed
SPEED = 30


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
        
       
    
def pickup_object(letter):
    # [ move to object ]
    mc.release_servo(3)
    mc.release_servo(4)
    input("Hold onto robot arm. Press any key to continue")
    mc.release_all_servos()     # manually release to desired object   
    input("Place robot mouth onto object. Press any key to continue")
    pump_on()
    sleep(2)
    neutral_pos()

def neutral_pos():
    # Return to neutral position
    mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=SPEED)
    #mc.sync_send_coords(coords=NEUTRAL_POS_COORDS,speed=SPEED)




"""
======Main function======
"""
def main(received):

    # Reset robot arm to neutral position
    print("Resetting robot")
    mc.set_color(128,128,128) #  reset to grey color
    pump_off()
    neutral_pos()


    # [ Get input for letter (via hand gesture) and bin]
    LETTER = 'center'#input("Input letter: ")
    BIN = received
    print("Inputs:",BIN,LETTER)
    
    # [ If object seen starts with [letter], pick up ]
    print("Picking up object")
    pickup_object(LETTER)

    # [ Pick up object, move to bin, drop object in bin]
    print("\nMoving to Bin", BIN)
    sleep(1)
    move_to_bin(BIN)
    sleep(1)
    print("Releasing block")
    pump_off()
    mc.set_color(128,128,128) #  reset to grey color
    sleep(1)
    
    print("Returning to base position")
    neutral_pos()

    print("waiting for input")



    ### test code
    # i = 7
    # #loop 7 times
    # while i > 0:                            
    #     mc.set_color(0,0,255) #blue light on
    #     sleep(2)    #wait for 2 seconds                
    #     mc.set_color(255,0,0) #red light on
    #     sleep(2)    #wait for 2 seconds
    #     mc.set_color(0,255,0) #green light on
    #     sleep(2)    #wait for 2 seconds
    #     i -= 1
    ### end of test code


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
        print("waiting for input")
        while True:
            received = ser.readline().decode().strip()  # Read incoming data
            
            if received:
                print("Received:", received)
                ser.write(b"Message received.\n" + received.encode() + b'\n')  # Send acknowledgment
                
                print(type(received))
                # run main loop
                main(received)

                
    
    except KeyboardInterrupt:
        # interrupt through CTRL + C
        # will turn off pump, return to neutral position, then display output message
        print("\nReturning to neutral")
        pump_off()
        neutral_pos()
    finally:
        print("Goodbye!\n== END OF SCRIPT===")
