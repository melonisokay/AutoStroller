from rpi_hardware_pwm import HardwarePWM
from gpiozero import DigitalOutputDevice, Button, MCP3008, LED
from time import sleep
import time
import signal
import _thread
import threading
import spidev

### MACROS
FORWARD = 1
REVERSE = 2
STOPPED = 3

###FUNCTIONS
# function linear variation of speed
def Speed_control(current_value, ideal_value, time_limit):
    slope = -1*(current_value-ideal_value)/time_limit
    for i in range(1, 2*time_limit+1):          # cycles along decreasing linear equation
        duty_cycle = round(slope* (i/2) + current_value, 2)
        print(f"{i} Duty Cycle {duty_cycle}")
        PWM0.start(duty_cycle)
        PWM1.start(duty_cycle)
        time.sleep(0.5)

def Read_Channel_0(channel):
    adc = spi.xfer2([1,(8+channel)<<4,0])
    Potdata = ((adc[1]&3) << 8) + adc[2]
    return Potdata

# Button functions
# When the button is pressed, allowing reading from the pot
def Bail_pressed():
    global i, pot_reading
    i += 1
    pot_reading = True
    print(f"button is pressed {i}\n")
# When the button is released, throw a interrupt prevent reading of pot
def Bail_released():
    global i, pot_reading
    i+=1
    pot_reading = False
    print(f"button is released {i}\n")
    _thread.interrupt_main()

DIR1_PIN = 16  # DIR control for motor 1 on pin GPIO16
DIR2_PIN = 6   # DIR control for motor 2 on pin GPIO6
MAGNET_PIN1 = 15 # PWM SIGNAL FOR M1
MAGNET_PIN2 = 18 # PWM SIGNAL FOR M2
BAIL_PIN = 5 # Bail Bar control simulated on GPIO5

BailBar = Button(BAIL_PIN, pull_up = True, bounce_time = 0.3)
# MD30C R2 SETUP
PWM0 = HardwarePWM(pwm_channel=0, hz=18000) # GPIO12
PWM1 = HardwarePWM(pwm_channel=1, hz=18000) # GPIO13
MAG15 = LED(MAGNET_PIN1)
MAG18 = LED(MAGNET_PIN2)
MAG15.on()
MAG18.on()

# NOTE: DIR off = clockwise, DIR on = couter-clockwise
DIR1 = DigitalOutputDevice(DIR1_PIN) # initially off
DIR2 = DigitalOutputDevice(DIR2_PIN)

pot_reading = True
BailBar.when_pressed = Bail_pressed
BailBar.when_released = Bail_released

# MCP3008 ADC Setup for channel 0
spi = spidev.SpiDev()
spi.open(0,0) # Open SPI bus
spi.max_speed_hz = 1800000 # recommended SPI clock frequency for range 2.7<voltage<3.3
# while(i <= 10):
#     currentdis = Read_Channel_0(0)
#     print(f"{currentdis}")
#     time.sleep(0.5)
#     i = i + 0.5
# spi.close()


### Test logic loop
### Summary of logics from left to right with increasing distance
### Forward: speed up, ideal, slow down, stop
### Reverse: slow down, ideal, speed up, stop
# NOTE increment to duty cycle after stop
duty = 20
Speed_control(0, duty, 5)
mode = FORWARD
i = 0

while True:
    try:
        while pot_reading: # Continuous loop
            currDis = Read_Channel_0(0)/105
            
            rangeMax = 9   # Distance in inches
            rangeMin = 1
            ideal = (rangeMax+rangeMin)/2
            bufferDis = 1.5
            dutyINCRE = 2.5
        
            print(f"Distance is {currDis}")
            # If distance is within stop zone for FORWARD and REVERSE and if mode = STOPPED
            if (mode == FORWARD and currDis > rangeMax-bufferDis and currDis <= rangeMax
                or mode == REVERSE and currDis >= rangeMin and currDis < rangeMin+bufferDis
                or mode == STOPPED):                        # Distance less than rangeMin
                print("stop and observe")
                # change previous distacnce value if starting from FORWARD and REVERSE
                if mode != STOPPED:
                    Speed_control(duty, 0, 5)
                    previous = currDis 
                updatedDis = Read_Channel_0(0)/105
                if updatedDis - previous >= 1:
                    DIR1.on() # change direction
                    DIR2.on()
                    mode = REVERSE
                    duty = 20
                    Speed_control(0, duty, 5)
                    
                elif updatedDis - previous <= -1:
                    mode = FORWARD
                    DIR1.off()
                    DIR2.off()
                    duty = 20
                    Speed_control(0, duty, 5)
                    #Dir1.off()
                    #Dir2.off()
                elif updatedDis - previous < 1 and updatedDis - previous > -1:
                    mode = STOPPED
                    duty = 0
                time.sleep(1)
                print(f"mode = {mode}")
                print("")
            # Distance is within ideal range and does not need speed manipulated
            elif currDis <= ideal+0.2 and currDis >= ideal-0.2:       # Within ideal distance +- 1
                print("within range do nothing")                    # Keep at same duty cycle
                time.sleep(1)
            # Distance in upper range (forward = slower, reverse = faster)
            elif mode == FORWARD:
                if currDis > ideal+0.2 and currDis <= rangeMax-bufferDis:
                    print("forward  decrease")                       # Close Distance
                    if duty == 0:
                        duty = 0
                    else:
                        duty = duty-dutyINCRE
                elif currDis >= rangeMin and currDis < ideal-0.2:
                    print("forward  increase speed")
                    duty = duty+dutyINCRE
                elif currDis >= rangeMax or currDis <= rangeMin:  
                    print("Exceeded Distance Range Stopping")     
                    Speed_control(duty, 0, 6)
                    duty = 0
                    #mode = STOPPED
                    #previous = currDis
                time.sleep(1)
            elif mode == REVERSE:
                if currDis > ideal+0.2 and currDis <= rangeMax:
                    print("reverse  increase speed")
                    duty = duty+dutyINCRE
                elif currDis <ideal-0.2 and currDis >= rangeMin+bufferDis:
                    print("reverse  decrease")
                    if duty == 0:
                        duty = 0
                    else:
                        duty = duty-dutyINCRE
                elif currDis >= rangeMax or currDis <= rangeMin:  # Distance greater than min and max range
                    print("Exceeded Distance Range Stopping")     # Stop Stroller within 5 second
                    Speed_control(duty, 0, 6)
                    duty = 0
                    #mode = STOPPED
                    #previous = currDis
                time.sleep(1)
            PWM0.start(duty)
            PWM1.start(duty)
            # If we go outside min and max range 
            # NOTE decide what to do with stopp outside range
            
            print(f"duty is {mode} {duty}")
            
    except KeyboardInterrupt:
        print(f"interrupt caught {i}")
        i = i+1
        # PWM1.value = 0
        # PWM2.value = 0
        PWM0.start(0)
        PWM1.start(0)
        MAG15.off()
        MAG18.off()
            
        if i >= 5:      # Prevent us from being stuck in the while loop. Could use a different signal or interrupt instead later
            break
        continue

spi.close()
MAG15.close()
MAG18.close()
