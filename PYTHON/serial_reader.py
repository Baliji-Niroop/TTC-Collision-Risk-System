import serial
import time

ser = serial.Serial("COM3", 115200)

while True:
    line = ser.readline().decode().strip()
    print(line)