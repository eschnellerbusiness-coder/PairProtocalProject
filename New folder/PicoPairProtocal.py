# Pico-to-Pico PWM Communication Protocol
# Either Pico can be Controller (A) or Responder (B)
# UART1: TX=GP8, RX=GP9 | PWM=GP15 | ADC=GP26

from machine import Pin, UART, PWM, ADC
from time import sleep, ticks_ms, ticks_diff

# ---- CONFIG ----
uart = UART(1, baudrate=9600, tx=Pin(8), rx=Pin(9))
adc = ADC(26)
pwm = PWM(Pin(15))
pwm.freq(1000)

def send(cmd, value):
    uart.write(f"{cmd},{value}\n")

def recv(timeout_ms=100):
    start = ticks_ms()
    while ticks_diff(ticks_ms(), start) < timeout_ms:
        if uart.any():
            line = uart.readline()
            if line:
                try:
                    return line.decode().strip()
                except:
                    pass
    return None

def read_adc_avg(samples=20):
    vals = [adc.read_u16() for _ in range(samples)]
    return sum(vals) / len(vals)

# ---- Role detection ----
print("Booting, waiting for UART traffic...")
msg = recv(timeout_ms=3000)
role = "responder" if msg else "controller"
print("Role:", role.upper())
sleep(1)

duty = 16384
direction = 1

# ---- Main loop ----
while True:
    if role == "controller":
        pwm.duty_u16(duty)
        send("SET", duty)
        resp = recv(timeout_ms=1500)
        if resp and resp.startswith("MEAS"):
            try:
                _, meas_str = resp.split(",")
                meas = float(meas_str)
                send("TRUE", duty)
                acc = 100 * (1 - abs(meas - duty) / max(duty, 1))
                print(f"Desired {duty:.0f} | Measured {meas:.0f} | {acc:.2f}%")
            except:
                pass
        else:
            role = "responder"
            sleep(1)
            continue
        duty += 8192 * direction
        if duty >= 65535:
            duty, direction = 65535, -1
        elif duty <= 0:
            duty, direction = 0, 1
        sleep(1)

    else:  # responder
        msg = recv(timeout_ms=500)
        if msg:
            try:
                cmd, val_str = msg.split(",")
                val = float(val_str)
                if cmd == "SET":
                    meas = read_adc_avg()
                    send("MEAS", meas)
                elif cmd == "TRUE":
                    acc = 100 * (1 - abs(meas - val) / max(val, 1))
                    print(f"True {val:.0f} | Measured {meas:.0f} | {acc:.2f}%")
            except:
                pass
        else:
            role = "controller"
            sleep(1)
