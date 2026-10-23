# ECE 4960
# Team 7: AutoStroller 
# Sam Gue, Lydia Heath, Gabriel Ruiz, Marilyn Turner, and Sabrina Weng
#
# This python script contains the software necessary for AutoStroller functionality.
#
# to run: python main.py

from enum import Enum
from rpi_hardware_pwm import HardwarePWM
from gpiozero import DigitalOutputDevice, Button, MCP3008
from time import sleep
import time
import signal
import _thread
import threading
import spidev

###################### Macros ######################
DIR0_PIN = 16  # DIR control for motor 1 on pin GPIO16
DIR1_PIN = 6   # DIR control for motor 2 on pin GPIO6
BAIL_PIN = 5 # Bail Bar control simulated on GPIO5
RELAY_PIN = 27 # Relay test on GPIO27
#REED_PIN = 17 # Bail bar control simulated on GPI017
#MODE_PIN = XX # Mode switch input from GPIOXX

###################### Enums ######################

class Mode(Enum):
    MANUAL = 1
    PUSH_ASSIST = 2
    AUTO = 3

###################### Globals ######################
i = 0   
bailEngaged = False
dutyCycle = 0

###################### Code ######################

# main(): Determines and executes the correct main operating loop for mode of the 
#         stroller.
#
# parameters: none
# returns: none
# 
# note: none
def main():
    print("Hello, World!")
    initialize()
    mode = determineMode()

    match mode:
        case MANUAL:
            manual()
        case PUSH_ASSIST:
            pushAssist()
        case AUTO:
            autonomous()
        case _:
            # default
            manual()

# initialize(): Initializes devices necessary for general stroller operation.
#
# parameters: none
# returns: none
# 
# note: none
def initialize():
    print("initializing...")

# determineMode(): Determines the mode of the stroller based on the position of the mode switch.
#
# parameters: none
# returns: mode enum
# 
# note: none
def determineMode():
    return Mode.MANUAL

# initSensors(): Initializes the radar and UWB sensors for autonomous mode.
#
# parameters: none
# returns: none
# 
# note: none
def initSensors():
    print("initializing sensors...")

# manual(): Executes the main operating loop for manual mode.
# 
# parameters: none
# returns: none
# 
# note: none
def manual():
    print("entering manual mode...")
    # Engage clutch
    # Brake motors
    # While running:
    #   wait for bail bar
    #   disengage clutch when bail bar engages
    #   monitor bail bar and engage clutch if bail bar disengages

# pushAssist(): Executes the main operating loop for push-assist mode.
# 
# parameters: none
# returns: none
# 
# note: none
def pushAssist():
    print("entering push-assist mode...")

    # SETUP GPIO
    PWM0 = HardwarePWM(pwm_channel=0, hz=18000) # GPIO12
    PWM1 = HardwarePWM(pwm_channel=1, hz=18000) # GPIO13

    # NOTE: DIR off = clockwise, DIR on = couter-clockwise
    DIR0 = DigitalOutputDevice(DIR0_PIN) # initially off
    DIR1 = DigitalOutputDevice(DIR1_PIN)

    # NOTE: Button is pulled high by default through internal pull-up resistor on pi
    #       Connect other side to ground. See website linked in research sources for more info 
    BailBar = Button(BAIL_PIN, pull_up = True, bounce_time = 0.3)
    BailBar.when_pressed = Bail_pressed
    BailBar.when_released = Bail_released

    Relay = DigitalOutputDevice(RELAY_PIN)

    # PUSH-ASSIST MAIN OPERATING LOOP
    while True:
        try:
            # Set dutyCycleValue
            getDriveBar() 
            print(f"Duty Cycle: {dutyCycle}")

            # Drive motors
            PWM0.start(dutyCycle)
            PWM1.start(dutyCycle)
            time.sleep(0.5)
        except KeyboardInterrupt:
            print("INTERRUPT!")
            brake()

        if i >= 4:
            break
        continue

    spi.close*()
    signal.pause()

# getDriveBar(): Determines the value of global dutyCycle as a result of the position of the 
#                drive bar.
# 
# parameters: none
# returns: none
# 
# note: Uses spi to read the value of the potentiometer connected to drive bar.
def getDriveBar():
    global dutyCycle

    adc = spi.xfer2([1,8<<4,0])
    potData = ((adc[1]&3)<<8) + adc[2]
    dutyCycle = (potData / 1023) * 100 # ADC calculation and duty cycle conversion
    

# autonomous(): Executes the main operating loop for autonomous mode.
# 
# parameters: none
# returns: none
# 
# note: none
def pushAssistMotors():
    print("driving motors according to drive bar input...")

# brake(): Engages emergency brakes.
# 
# parameters: none
# returns: none
# 
# note: none
def brake():
    global dutyCycle
    currentValue = dutyCycle
    timeLimit = 5      # 5 second limit for motor to stop
    print("braking...")
    slope = -1*currentValue/timeLimit
    for i in range(1, 2*timeLimit+1):          # cycles along decreasing linear equation
        dutyCycle = round(slope* (i/2) + currentValue, 2)
        print(f"{i} Duty Cycle {dutyCycle}")
        PWM0.start(dutyCycle)
        PWM1.start(dutyCycle)
        time.sleep(0.5)
    print("Motors stopped")

    # prompt user to pull down bail bar if in push-assist or manual mode
    # inform user that the path is obstructed if in autonomous mode 


# isBailEngaged(): Determines whether or not the bail bar is engaged.
# 
# parameters: none
# returns: true if bail bar engaged, false if not
# 
# note: none
def isBailEngaged():
    return False


# autonomous(): Executes the main operating loop for autonomous mode.
# 
# parameters: none
# returns: none
# 
# note: none
def autonomous():
    print("entering autonomous mode...")

# isTethered(): Determines whether or not the stroller is tethered to the person by reading the 
#               state of the reed switch.
# 
# parameters: none
# returns: true if the reed switch is closed, false if open
# 
# note: none
def isTethered():
    return False

# isPathClear(): Determines whether or not the path is clear by getting feedback from radar sensor.
# 
# parameters: none
# returns: true if the path is clear, false if not
# 
# note: none
def isPathClear():
    return False

# brakesEngaged(): Determines whether or not the brakes are currently engaged.
# 
# parameters: none
# returns: true if the brakes are engaged, false if not
# 
# note: none
def brakesEngaged():
    return False

# engageBrakes(): Engages/disengages the emergency brakes.
# 
# parameters: True if engaging brakes, False if disengaging brakes
# returns: true if the brakes are engaged, false if not
# 
# note: none
def engageBrakes(engage):
    if engage:
        print("engage emergency brakes")
    else:
        print("disengage emergency brakes")

# autoMotors(): Implements the motor control feedback loop for autonomous mode according to the 
#               distance of the person as reported by the UWB module.
# 
# parameters: True if engaging brakes, False if disengaging brakes
# returns: true if the brakes are engaged, false if not
# 
# note: none
def autoMotors():
    print("driving motors according to position of person")


if __name__ == "__main__":
    main()