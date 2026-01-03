import cv2
import numpy as np

# Circularity-based ROI detection (edge + shape filter)
MIN_AREA_RATIO = 0.015
MIN_CIRCULARITY = 0.65

def auto_roi(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (9, 9), 0)

    # Edge detection to find object contours (more stable)
    edges = cv2.Canny(gray, 50, 150)

    kernel = np.ones((3,3), np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=2)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None, None, None

    cnt = max(contours, key=cv2.contourArea)

    frame_area = frame.shape[0] * frame.shape[1]
    area = cv2.contourArea(cnt)

    if area < MIN_AREA_RATIO * frame_area:
        return None, None, None

    perimeter = cv2.arcLength(cnt, True)
    if perimeter == 0:
        return None, None, None

    circularity = 4 * np.pi * area / (perimeter * perimeter)

    if circularity < MIN_CIRCULARITY:
        return None, None, None

    x, y, w, h = cv2.boundingRect(cnt)
    roi = frame[y:y+h, x:x+w]

    # Return circularity as the third value for compatibility with main.py
    return roi, (x, y, w, h), circularity
