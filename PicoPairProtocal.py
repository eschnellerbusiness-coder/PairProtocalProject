from machine import Pin, PWM, UART, ADC
import utime

# ======= Configuration =======
PWM_PIN = 15
ADC_PIN = 26
UART_TX = 0
UART_RX = 1
MODE_PIN = 14  # Determines if device is Generator or Monitor
BAUD = 9600
VREF = 3.3

# ======= Initialize Hardware =======
mode_select = Pin(MODE_PIN, Pin.IN, Pin.PULL_DOWN)
uart = UART(0, baudrate=BAUD, tx=Pin(UART_TX), rx=Pin(UART_RX))
role = "GENERATOR" if mode_select.value() == 1 else "MONITOR"

print(f"Running as: {role}")

# ======= Generator Mode =======
def run_generator():
    pwm = PWM(Pin(PWM_PIN))
    pwm.freq(1000)
    
    while True:
        for duty in range(0, 101, 10):
            # Set PWM duty
            pwm.duty_u16(int(duty * 65535 / 100))
            uart.write(f"{duty}\n")
            print(f"Sent Duty: {duty}%")
            
            # Wait for feedback
            timeout = utime.ticks_ms() + 2000
            while utime.ticks_ms() < timeout:
                if uart.any():
                    try:
                        data = uart.readline()
                        measured = float(data.decode().strip())
                        error = duty - measured
                        print(f"Measured: {measured:.2f}% | Error: {error:+.2f}%")
                        break
                    except:
                        pass
                utime.sleep(0.05)
            
            utime.sleep(1)


# ======= Monitor Mode =======
def run_monitor():
    adc = ADC(Pin(ADC_PIN))
    while True:
        if uart.any():
            try:
                data = uart.readline()
                duty_expected = int(data.decode().strip())

                # Measure analog voltage
                reading = adc.read_u16()
                voltage = (reading / 65535) * VREF
                measured_duty = (voltage / VREF) * 100

                uart.write(f"{measured_duty:.2f}\n")
                print(f"Recv:{duty_expected}%  Measured:{measured_duty:.2f}%")
            except:
                pass
        utime.sleep(0.1)

# ======= Run Appropriate Mode =======
try:
    if role == "GENERATOR":
        run_generator()
    else:
        run_monitor()
except KeyboardInterrupt:
    print("Program stopped.")
