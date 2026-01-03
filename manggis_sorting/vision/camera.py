import cv2
import time

class Camera:
    def __init__(self, index=0):
        # Paksa backend DirectShow (PALING STABIL di Windows)
        self.cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

        # Kasih waktu kamera untuk inisialisasi
        time.sleep(1.0)

        if not self.cap.isOpened():
            raise RuntimeError(f"Camera index {index} could not be opened")

        # Optional tapi disarankan
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    def read(self):
        if self.cap is None:
            return False, None
        return self.cap.read()

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        cv2.destroyAllWindows()
