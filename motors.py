# ECE 4960
# Motor control
# Samuel Gue, Lydia Heath, Gabriel Ruiz, Marilyn Turner, Sabrina Weng

from rpi_hardware_pwm import HardwarePWM
from gpiozero import PWMOutputDevice, DigitalOutputDevice, Button, MCP3008
from time import sleep
import time
import signal
import _thread
import threading
import spidev

###################### Macros ######################
PWM1_PIN = 12  # PWM control for motor 1 on pin GPIO12
PWM2_PIN = 13  # PWM control for motor 2 on pin GPIO13
DIR1_PIN = 16  # DIR control for motor 1 on pin GPIO16
DIR2_PIN = 6   # DIR control for motor 2 on pin GPIO6
BAIL_PIN = 5 # Bail Bar control simulated on GPIO5
RELAY_PIN = 27 # Relay test on GPIO27
#REED_PIN = 17 # Bail bar control simulated on GPI017
DUTY_CYCLE = 0.25
FREQUENCY = 10000


###################### Code ######################

# MCP3008 ADC Setup for channel 0
spi = spidev.SpiDev()
spi.open(0,0) # Open SPI bus
spi.max_speed_hz = 1800000 # recommended SPI clock frequency for range 2.7<voltage<3.3

# PWM1 = PWMOutputDevice(pin=PWM1_PIN, active_high=True, frequency = FREQUENCY) # Initial frequency = 100Hz
# PWM2 = PWMOutputDevice(pin=PWM2_PIN, active_high=True, frequency = FREQUENCY)
PWM0 = HardwarePWM(pwm_channel=0, hz=18000)
PWM1 = HardwarePWM(pwm_channel=1, hz=18000)

# NOTE: DIR off = clockwise, DIR on = couter-clockwise
DIR1 = DigitalOutputDevice(DIR1_PIN) # initially off
DIR2 = DigitalOutputDevice(DIR2_PIN)

# NOTE: Button is pulled high by default through internal pull-up resistor on pi
#       Connect other side to ground. See website linked in research sources for more info 
BailBar = Button(BAIL_PIN, pull_up = True, bounce_time = 0.3)
#ReedSwitch = Button(REED_PIN, pull_up = True, bounce_time = 0.3)
# Pot = MCP3008(channel = 0, device = 0)
Relay = DigitalOutputDevice(RELAY_PIN)

i = 0   
running_code = False
pot_reading = False

# Potentiometer functions
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

# Motor Functions
# Utilizes current value and linear equation to step down motor speed in 10 steps
def Slow_down(current_value):
    time_limit = 5          # 5 second limit for motor to stop
    print("Stopping Motor")
    slope = -1*current_value/time_limit
    for i in range(1, 2*time_limit+1):          # cycles along decreasing linear equation
        duty_cycle = round(slope* (i/2) + current_value, 2)
        print(f"{i} Duty Cycle {duty_cycle}")
        PWM0.start(duty_cycle)
        PWM1.start(duty_cycle)
        time.sleep(0.5)
    print("Motors stopped")

# Use Estop.when_release when during press
# Use Estop.when_pressed when it releases
# Backwards due to normally closed button

# Estop.when_released = Button_pressed 
BailBar.when_pressed = Bail_pressed
BailBar.when_released = Bail_released
#ReedSwitch.when_pressed = Bail_pressed
#ReedSwitch.when_released = Bail_released

#Testing Relay, can be deleted
Relay.on()
time.sleep(5)
Relay.off()

while True: # Continuous loop
    try:
        while pot_reading:  # Selected with Bail_pressed to read pot
            dutycyclevalue = Read_Channel_0(0)
            DUTY_CYCLE = dutycyclevalue / 1023 # ADC calculation
            print(f"Pot value: {DUTY_CYCLE}")
            # PWM1.value = DUTY_CYCLE
            # PWM2.value = DUTY_CYCLE
            PWM0.start(DUTY_CYCLE*100)      # Send Hardware PWM to motors
            PWM1.start(DUTY_CYCLE*100)
            time.sleep(.5)
    except KeyboardInterrupt:
        print("interrupt caught")
        Slow_down(DUTY_CYCLE*100)   # Button was released and motor slows down
        # PWM1.value = 0
        # PWM2.value = 0
        # DUTY_CYCLE = DUTY_CYCLE/2
        # PWM0.start(DUTY_CYCLE)
        # PWM1.start(DUTY_CYCLE)
        # time.sleep(1)
            

        if i >= 4:      # Prevent us from being stuck in the while loop. Could use a different signal or interrupt instead later
            break
        continue


spi.close()
# while True:
#     try:
#         while pot_reading:
#             print(f"Pot value: {Pot.value}") # Reads pot values
#             duty_cycle = round(Pot.value, 2)
#             PWM1.value = 1 - duty_cycle
#             PWM2.value = 1 - duty_cycle
#             time.sleep(5)
#     except KeyboardInterrupt:
#         print("interrupt caught")

#         Slow_down(duty_cycle)

#         if i >= 2:
#             break
#         continue

# while True:
#     if not Estop.is_pressed:
#         print("Button is pressed")
#     else:
#         print("Button is not pressed")


# Drive motors
# PWM1.on()
# PWM2.on()
# PWM1.value = 0
# PWM2.value = 0
#for remaining in range (30, 0, -1):
#    PWM.blink(on_time=DUTY_CYCLE*(1/FREQUENCY), off_time=(1-DUTY_CYCLE)*(1/FREQUENCY))
#    print(f"secs: {remaining}")
#    time.sleep(1)
#PWM.off()


while running_code:
    time.sleep(5)
    PWM1.value = DUTY_CYCLE
    PWM2.value = DUTY_CYCLE
    time.sleep(5)
    PWM1.value = .5
    PWM2.value = .5
    time.sleep(5)
    PWM1.value =.75
    PWM2.value =.75
    time.sleep(5)
    PWM1.value = .8
    PWM2.value = .8
    time.sleep(5)

# PWM1.blink(fade_out_time = 0)
# PWM2.blink(fade_out_time = 0)
    

# PWM1.off()
# PWM2.off()



signal.pause()
#exit()



