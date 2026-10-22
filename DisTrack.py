import time

# function linear variation of speed
def Speed_control(current_value, ideal_value, time_limit):
    slope = -1*(current_value-ideal_value)/time_limit
    for i in range(1, 2*time_limit+1):          # cycles along decreasing linear equation
        duty_cycle = round(slope* (i/2) + current_value, 2)
        print(f"{i} Duty Cycle {duty_cycle}")
        #PWM0.start(duty_cycle)
        #PWM1.start(duty_cycle)
        time.sleep(0.5)
        #MAG15.off()
        #MAG18.off()


duty = 50
while True:  # Continuous loop until "exit"
    while True: # Wait for valid float input
        try:
            currDis = float(input("distance between devices: "))
            break
        except ValueError:
            print("Not a valid Number.")

    rangeMax = 24   # Distance in inches
    rangeMin = 18
    ideal = (rangeMax+rangeMin)/2

    print(f"Distance is {currDis}")
    if currDis <= ideal+1 and currDis >= ideal-1:   # Within ideal distance +- 1
        print("within range do nothing")
    elif currDis > ideal+1 and currDis <= rangeMax:   # More distance than ideal but not out MAX range
        print("decrease speed")                       # Close Distance
        duty = duty-5
        #PWM0.start(duty)
        #PWM1.start(duty)
        time.sleep(0.5)
        #MAG15.off()
        #MAG18.off()
    elif currDis < ideal-1 and currDis > rangMin:   # Less distance than ideal but not lower than MIN range
        print("increase speed")                     # Increase Distance
        duty = duty + 5
        #PWM0.start(duty)
        #PWM1.start(duty)
        time.sleep(0.5)
        #MAG15.off()
        #MAG18.off()
    elif currDis > rangeMax:                        # Distance greater than Max eg running away
        print("Exceeded Max Distance Stopping")     # Stop Stroller within 5 second
        Speed_control(duty, 0, 5)
    elif currDis < rangeMin:                        # Distance less than rangeMin
        print("going backward")
        #PWM0.start(duty)
        #PWM1.start(duty)
        time.sleep(0.5)
        #MAG15.off()
        #MAG18.off()
    print(f"duty is {duty}")
    # if input("exit? ") == "exit":
    #     break

#Battery Monitor Testing


