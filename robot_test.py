from pymycobot.mycobot import MyCobot

from pymycobot import PI_PORT, PI_BAUD
import time

# Create object code here for Raspberry Pi version
mc: MyCobot = MyCobot(port=PI_PORT, baudrate=str(PI_BAUD))


# Check whether the program can be burned into the robot arm
if mc.is_controller_connected() != 1:
    print("Please connect the robot arm correctly for program writing")
    exit(0)





# =========PROGRAM CODE============

# Positions
NEUTRAL_POS_COORDS = [57.5, -64.4, 408.6, -92.37, 0.17, -89.83]
BIN_A_COORDS = [103.6, 75.2, 402.2, -88.15, 1.71, -24.46]
BIN_B_COORDS = [21.4, 130.1, 390.6, -84.67, 17.07, 19.83]
BIN_C_COORDS = [105.3, -110.7, 349.8, -83.04, 16.89, -112.61]
BIN_D_COORDS = [73.1, -124.9, 393.2, -92.03, 6.24, -124.85]
LOADING_ZONE_COORDS = [119.8, 33.7, 380.3, -81.99, 3.74, -43.88]
# Set speed
SPEED = 30

def main():
    """
    Main function performs some action
    """

    # Reset robot arm to neutral position
    mc.send_coords(coords=NEUTRAL_POS_COORDS, speed=SPEED)

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

if __name__ == "__main__":
    main()