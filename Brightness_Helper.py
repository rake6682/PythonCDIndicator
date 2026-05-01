#!/usr/bin/env python3
"""
Simple helper: prints mouse x,y and the sampled screen pixel brightness (and raw RGB).
Requires: PyQt5, pynput

Run: python3 mouse_brightness_logger.py
Press Ctrl-C to quit.
"""
import sys
import time
from threading import Event

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QGuiApplication
from pynput import mouse

# Rate limit (seconds) for printing while moving
PRINT_INTERVAL = 0.05

def get_pixel_color_and_brightness(screen, x, y):
    """
    Sample the screen at logical coords (x,y), account for devicePixelRatio,
    return (r,g,b,brightness,dev_x,dev_y,dpr).
    Brightness = average of R,G,B (0-255).
    """
    x_int = int(round(x))
    y_int = int(round(y))
    # grabWindow expects device pixels; width/height 1x1
    img = screen.grabWindow(0, x_int, y_int, 1, 1).toImage()
    color = img.pixelColor(0, 0)
    r, g, b = color.red(), color.green(), color.blue()
    brightness = (r + g + b) / 3.0
    return r, g, b, brightness, x_int, y_int

def main():
    app = QApplication(sys.argv)  # needed for QGuiApplication.primaryScreen()
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        print("No primary screen detected. Exiting.")
        return

    stop_event = Event()
    last_print = 0.0

    # def on_move(x, y):
    #     nonlocal last_print
    #     now = time.time()
    #     if now - last_print < PRINT_INTERVAL:
    #         return
    #     last_print = now

    #     try:
    #         r, g, b, brightness, dev_x, dev_y, dpr = get_pixel_color_and_brightness(screen, x, y)
    #         print(f"x={x} y={y} | dev_x={dev_x} dev_y={dev_y} dpr={dpr:.2f} | "
    #               f"R={r} G={g} B={b} | brightness={brightness:.2f}")
    #     except Exception as e:
    #         print("Sample error:", e)

    def on_click(x, y, button, pressed):
        # Print an immediate sample on click (pressed only)
        if pressed:
            try:
                r, g, b, brightness, x_int, y_int = get_pixel_color_and_brightness(screen, x, y)
                print(f"[click] x={x_int} y={y_int} |"
                      f"R={r} G={g} B={b} | brightness={brightness:.2f}")
            except Exception as e:
                print("Sample error on click:", e)

    listener = mouse.Listener(on_click=on_click)
    listener.start()

    print("Mouse brightness logger running. Move the mouse to see samples. Ctrl-C to quit.")
    try:
        while not stop_event.is_set():
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        print("Exiting.")

main()
