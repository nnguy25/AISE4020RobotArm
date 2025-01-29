from pymycobot.mycobot import MyCobot

from pymycobot import PI_PORT, PI_BAUD
import time

# Create object code here for Raspberry Pi version
mc = MyCobot(PI_PORT, PI_BAUD)


# Check whether the program can be burned into the robot arm
if mc.is_controller_connected() != 1:
    print("Please connect the robot arm correctly for program writing")
    exit(0)


i = 7
#loop 7 times
while i > 0:                            
    mc.set_color(0,0,255) #blue light on
    time.sleep(2)    #wait for 2 seconds                
    mc.set_color(255,0,0) #red light on
    time.sleep(2)    #wait for 2 seconds
    mc.set_color(0,255,0) #green light on
    time.sleep(2)    #wait for 2 seconds
    i -= 1