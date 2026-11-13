# ECE 4960
# Camera Display
# Samuel Gue, Lydia Heath, Gabriel Ruiz, Marilyn Turner, Sabrina Weng

import glob
import tkinter as tk
import cv2
from PIL import Image, ImageTk
from gpiozero import Button

import signal
import sys

def handle_sigint(sig, frame):
    print("\nCtrl+C detected. Cleaning up and exiting...")
    cap.release()
    root.destroy()
    sys.exit(0)

signal.signal(signal.SIGINT, handle_sigint)

SWITCH_PIN = 5  # GPIO 5 (Physical Pin 11)

def find_usb_camera():
    for device_path in sorted(glob.glob("/dev/video*")):
        cap = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print(f"Connected to USB webcam at {device_path}")
                return cap
            cap.release()
    return None

switch = Button(SWITCH_PIN, pull_up=True, bounce_time=0.05)
cap = find_usb_camera()
if cap is None:
    print("Error: No working USB webcam found.")
    exit()

cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

# Set up fullscreen Tkinter window
root = tk.Tk()
root.title("USB Webcam Live Feed")
root.configure(background="black")
root.attributes("-fullscreen", True)

label = tk.Label(root, bg="black")
label.pack(expand=True, fill="both")

window_visible = True

def update_loop():
    global window_visible

    # Display is ON when switch is released, OFF when pressed (connected to GND)
    should_show = not switch.is_pressed

    if should_show:
        if not window_visible:
            print("Switch OPEN -> Showing display")
            root.deiconify()
            root.attributes("-fullscreen", True)
            window_visible = True

        ret, frame = cap.read()
        if ret:
            # Resize frame to fit screen and convert BGR to RGB
            screen_w = root.winfo_screenwidth()
            screen_h = root.winfo_screenheight()
            frame = cv2.resize(frame, (screen_w, screen_h))
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = ImageTk.PhotoImage(image=Image.fromarray(rgb_frame))
            label.imgtk = img
            label.configure(image=img)
    else:
        if window_visible:
            print("Switch PRESSED -> Hiding display")
            root.withdraw()  # Cleanly hides the window on Wayland & X11
            window_visible = False
        cap.grab()  # Keep webcam buffer fresh while hidden

    # Run loop every 15ms (~60 FPS polling)
    root.after(15, update_loop)

def cleanup(event=None):
    cap.release()
    root.destroy()

root.bind("<Escape>", cleanup)
root.protocol("WM_DELETE_WINDOW", cleanup)

print("Running. Press Ctrl+C in terminal or Esc on keyboard to exit.")
try:
    update_loop()
    root.mainloop()
except KeyboardInterrupt:
    cleanup()
