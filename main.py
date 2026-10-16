# ECE 4960
# Team 7: AutoStroller 
# Sam Gue, Lydia Heath, Gabriel Ruiz, Marilyn Turner, and Sabrina Weng
#
# This python script contains the software necessary for AutoStroller functionality.
#
# to run: python main.py

from enum import Enum

class Mode(Enum):
    MANUAL = 1
    PUSH_ASSIST = 2
    AUTO = 3

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

# pushAssist(): Executes the main operating loop for push-assist mode.
# 
# parameters: none
# returns: none
# 
# note: none
def pushAssist():
    print("entering push-assist mode...")

# pushAssistMotors(): Implements the motor control feedback loop according to the position of the
#                     drive bar.
# 
# parameters: none
# returns: none
# potentiometer reading.
# 
# parameters: none
# returns: position of the drive bar as percentage
# 
# note: none
def getDriveBar():
    return 0

# autonomous(): Executes the main operating loop for autonomous mode.
# 
# parameters: none
# returns: none
# 
# note: none
def pushAssistMotors():
    print("driving motors according to drive bar input...")

# pushAssistBrake(): Engages emergency brakes for push-assist mode and prompts user to pull down 
#                    the bail bar.
# 
# parameters: none
# returns: none
# 
# note: none
def pushAssistBrake():
    print("braking...")

# isBailEngaged(): Determines whether or not the bail bar is engaged.
# 
# parameters: none
# returns: true if bail bar engaged, false if not
# 
# note: none
def isBailEngaged():
    return False

# getDriveBar(): Determines position of the drive bar according to potentiometer reading.
# 
# parameters: none
# returns: position of the drive bar as percentage
# 
# note: none
def getDriveBar():
    return 0

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