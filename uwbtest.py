#UWB Test 

import serial
import time

# Adjust port: "/dev/ttyACM0" for USB or "/dev/serial0" for GPIO pins
SERIAL_PORT = "/dev/serial0" 
BAUD_RATE = 115200

try:
    ser = serial.Serial(SERIAL_PORT, baudrate=BAUD_RATE, timeout=1)
    print(f"Connected to Qorvo Board on {SERIAL_PORT}")
    
    # Optional: Send awake or initialization commands if using CLI firmware
    ser.write(b"\r\r") 
    time.sleep(0.5)

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            
            # Case A: If your firmware outputs comma-separated text strings
            if "DIST" in line or "AN0" in line:
                print(f"Ranging Data: {line}")
                # Example split logic depending on your exact CLI format:
                # data = line.split(",")
                
            # Case B: Standard debug stream dump
            elif line:
                print(f"Raw Output: {line}")
                
        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting script.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'ser' in locals() and ser.is_open:
        ser.close()
