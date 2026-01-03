import cv2
import time
import threading

latest_frame = None
lock = threading.Lock()

def update_frame(frame):
    global latest_frame
    with lock:
        latest_frame = frame.copy()

def get_frame():
    with lock:
        return latest_frame
