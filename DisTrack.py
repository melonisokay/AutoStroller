import time

while True:  # Continuous loop until "exit"
    while True: # Wait for valid float input
        try:
            currDis = float(input("distance between devices: "))
            break
        except ValueError:
            print("Not a valid Number.")

    rangeMax = 20   # Arbituary ranges
    rangeMin = 10
    ideal = (rangeMax+rangeMin)/2
    time_slow = 2   # Time to slow down or increase
    print(f"Distance is {currDis}")
    if currDis < rangeMax and currDis > rangeMin:
        print("within range do nothing")
    elif currDis > rangeMax:
        print("decrease speed")
        slope = -1*(currDis-ideal)/time_slow
        print(f"slope: {slope}")
        for i in range(1, 2*time_slow+1):          # cycles along decreasing linear equation
                duty_cycle = round(slope* (i/2) + currDis, 2)
                print(f"{i} Duty Cycle {duty_cycle}")
                ##PWM0.start(duty_cycle)
                ##PWM1.start(duty_cycle)
                time.sleep(0.5)
                ##MAG15.off()
                ##MAG18.off()
    elif currDis < rangeMin:
        print("increase speed")
        slope = -1*(currDis-ideal)/time_slow
        print(f"slope: {slope}")
        for i in range(1, 2*time_slow+1):          # cycles along decreasing linear equation
                duty_cycle = round(slope* (i/2) + currDis, 2)
                print(f"{i} Duty Cycle {duty_cycle}") # need whole numbers
                ##PWM0.start(duty_cycle)
                ##PWM1.start(duty_cycle)
                time.sleep(0.5)
                ##MAG15.off()
                ##MAG18.off()

    if input("exit? ") == "exit":
        break

#Battery Monitor Testing


