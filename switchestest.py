# ECE 4960
# Test 3-position switch and new potentiometer values
# Samuel Gue, Lydia Heath, Gabriel Ruiz, Marilyn Turner, Sabrina Weng


# Potentiometer range: 0.3685 - 0.4379

from gpiozero import Button
import time

# Connect the two outer switch terminals to GPIO 19 and GPIO 20
# Connect the middle (common) terminal to Ground (GND)
pin_up = Button(19)
pin_down = Button(20)

def check_physical_switch():
    if pin_up.is_pressed:
        return "Manual Mode"
    elif pin_down.is_pressed:
        return "Autonomous Mode"
    else:
        # Neither pin is connected to ground, meaning the switch is in the center
        return "Push-Assist Mode"

while True:
    print(f"Current Mode: {check_physical_switch()}")
    time.sleep(0.5)

def Read_Channel_0(channel):
    adc = spi.xfer2([1,(8+channel)<<4,0])
    Potdata = ((adc[1]&3) << 8) + adc[2]
    return Potdata