while True:
    while True:
        try:
            currDis = float(input("distance between devices: "))
            break
        except ValueError:
            print("Not a valid Number.")

    rangeMax = 20
    rangeMin = 10
    print(f"Distance is {currDis}")
    if currDis < rangeMax and currDis > rangeMin:
        print("within range do nothing")
    elif currDis > rangeMax:
        print("decrease speed")
    elif currDis < rangeMin:
        print("increase speed")

    if input("exit? ") == "exit":
        break

