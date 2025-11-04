# UART Receiver - prints messages from other Pico
# TX=GP8, RX=GP9

from machine import UART, Pin
from time import sleep

uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
print("Receiver started. Waiting for messages...\n")

while True:
    if uart.any():
        msg = uart.readline()
        if msg:
            try:
                print("Received:", msg.decode().strip())
            except:
                print("Received unreadable data.")
    sleep(0.1)
