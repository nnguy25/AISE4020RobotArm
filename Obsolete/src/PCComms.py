import serial

# Replace '/dev/ttyGS0' with the correct serial device on the Pi
ser = serial.Serial('/dev/ttyGS0', 115200, timeout=1)

print("Raspberry Pi is ready to receive messages.")

while True:
    received = ser.readline().decode().strip()  # Read incoming data
    if received:
        
        print("Received:", received)

        ser.write(b"Message received.\n" + received.encode() + b'\n')  # Send acknowledgment
