import os
import cv2
import joblib
import time

from vision.camera import Camera
from vision.preprocess import extract_features
from vision.roi import auto_roi
from mqtt.mqtt_client import MQTTClient
from firebase.firebase_client import FirebaseClient
from config.config import *

# =====================================================
# DEVICE & GRADE MAPPING
# =====================================================
DEVICE_ID = "Python_Inference"

# Model output : 0=C, 1=B, 2=A
# Sistem grade : 1=A, 2=B, 3=C
MODEL_TO_GRADE = {
    0: 3,  # C → Grade 3
    1: 2,  # B → Grade 2
    2: 1   # A → Grade 1
}

GRADE_LABEL = {
    1: "A",
    2: "B",
    3: "C"
}

# =====================================================
# STATE MACHINE (ANTI DOUBLE COUNT)
# =====================================================
STATE_EMPTY = 0       # kotak kosong
STATE_DETECTING = 1   # buah masuk, stabilisasi
STATE_LOCKED = 2      # buah sudah dihitung (tunggu keluar)

state = STATE_EMPTY
detect_start = 0
last_state_change = 0

STABLE_TIME = 0.7     # deteksi harus stabil (detik)
EXIT_TIME = 1.0       # waktu tunggu buah keluar (detik)
DETECTION_PERSISTENCE = 1.5  # keep showing detection for this many seconds if frames drop

# hasil grading yang sudah di-lock
locked_grade = None
locked_label = None
# preview label shown during STABLE_TIME after initial detection
preview_label = None

# Last-seen tracking for persistence (avoid flicker when ROI briefly disappears)
last_presence = 0
last_roi = None
last_bbox = None
last_purple_ratio = None

# =====================================================
# LOAD MODEL
# =====================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "ml", "decision_tree_manggis.pkl")

# =====================================================
# MAIN (with diagnostics)
# =====================================================

def main():
    global state, detect_start, last_state_change, locked_grade, locked_label, last_status

    print(f"[*] Model path: {model_path}")
    try:
        model = joblib.load(model_path)
        print("[+] Model loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        raise

    # Local tracking variables (avoid UnboundLocalError) and preview state
    preview_label = None
    last_presence = 0
    last_roi = None
    last_bbox = None
    last_purple_ratio = None

    # Init hardware & services with diagnostics
    print("[*] Initializing camera...")
    camera = Camera(CAMERA_INDEX)
    ret, test_frame = camera.read()
    if not ret or test_frame is None:
        camera.release()
        raise RuntimeError("Camera could not read a frame. Check CAMERA_INDEX and camera connection.")
    print("[+] Camera OK")

    print("[*] Connecting to MQTT broker...")
    mqtt = MQTTClient(
        MQTT_BROKER,
        MQTT_PORT,
        MQTT_USERNAME,
        MQTT_PASSWORD
    )
    print("[+] MQTT client created (check broker for connection)")

    print("[*] Initializing Firebase client...")
    firebase = FirebaseClient(FIREBASE_URL)
    print("[+] Firebase client ready")

    last_status = 0

    try:
        # Main loop
        while True:
            ret, frame = camera.read()
            if not ret or frame is None:
                print("⚠️  Camera read failed; exiting main loop")
                break

            now = time.time()

            # MQTT heartbeat
            if now - last_status > 5:
                try:
                    mqtt.client.publish(
                        f"manggis/status/{DEVICE_ID}",
                        '{"status":"online"}'
                    )
                except Exception as e:
                    print(f"⚠️  MQTT publish failed: {e}")
                last_status = now

            # ROI detection (with persistence against brief dropouts)
            roi, bbox, purple_ratio = auto_roi(frame)

            # update last-seen if ROI present
            if roi is not None:
                last_presence = now
                last_roi = roi
                last_bbox = bbox
                last_purple_ratio = purple_ratio

            # if ROI briefly disappeared, keep using last values for a short time
            if roi is None and last_presence != 0 and (now - last_presence) < DETECTION_PERSISTENCE:
                roi = last_roi
                bbox = last_bbox
                purple_ratio = last_purple_ratio

            if roi is not None:
                if state == STATE_EMPTY:
                    state = STATE_DETECTING
                    detect_start = now

                    # quick preview prediction so a grade is shown immediately
                    try:
                        _features_arr, _ = extract_features(roi)
                        _pred = int(model.predict(_features_arr)[0])
                        _grade = MODEL_TO_GRADE[_pred]
                        preview_label = GRADE_LABEL[_grade]
                    except Exception:
                        preview_label = None

                elif state == STATE_DETECTING:
                    # Only finalize if object has been detected continuously (accounting for persistence)
                    if now - detect_start >= STABLE_TIME:
                        features_array, features_dict = extract_features(roi)

                        pred_model = int(model.predict(features_array)[0])
                        grade = MODEL_TO_GRADE[pred_model]
                        grade_label = GRADE_LABEL[grade]

                        locked_grade = grade
                        locked_label = grade_label
                        # clear preview after final classification
                        preview_label = None

                        # MQTT
                        try:
                            mqtt.publish_grade(TOPIC_GRADE, grade)
                        except Exception as e:
                            print(f"⚠️  publish_grade failed: {e}")

                        # Firebase
                        try:
                            firebase.update_last_grade(grade)
                            firebase.update_summary(grade)
                            firebase.add_grading_result(
                                device_id=DEVICE_ID,
                                grade=grade,
                                grade_label=grade_label,
                                features=features_dict,
                                roi=bbox,
                                purple_ratio=purple_ratio
                            )
                        except Exception as e:
                            print(f"⚠️  Firebase update failed: {e}")

                        state = STATE_LOCKED
                        last_state_change = now

                # Visual
                if bbox is not None:
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                    # If final locked label exists, show it; otherwise show preview label
                    if locked_label is not None:
                        text = f"Grade {locked_label}"
                        color = (0, 255, 0)
                    elif preview_label is not None:
                        text = f"Preview: Grade {preview_label}"
                        color = (0, 255, 255)
                    else:
                        text = None

                    if text is not None:
                        cv2.putText(
                            frame,
                            text,
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.8,
                            color,
                            2
                        )

            else:
                # If object has been lost for longer than persistence, handle exit
                if last_presence == 0 or (now - last_presence) >= DETECTION_PERSISTENCE:
                    if state == STATE_LOCKED and now - last_state_change >= EXIT_TIME:
                        state = STATE_EMPTY
                        locked_grade = None
                        locked_label = None

                    cv2.putText(
                        frame,
                        "Tidak ada manggis",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2
                    )
                else:
                    # within persistence window — show last known bbox/preview/locked
                    if last_bbox is not None:
                        x, y, w, h = last_bbox
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                        # show preview or locked accordingly
                        if locked_label is not None:
                            text = f"Grade {locked_label}"
                            color = (0, 255, 0)
                        elif preview_label is not None:
                            text = f"Preview: Grade {preview_label}"
                            color = (0, 255, 255)
                        else:
                            text = None

                        if text is not None:
                            cv2.putText(
                                frame,
                                text,
                                (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.8,
                                color,
                                2
                            )
                    else:
                        cv2.putText(
                            frame,
                            "Tidak ada manggis",
                            (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 0, 255),
                            2
                        )

            cv2.imshow("Manggis Sorting - Decision Tree", frame)

            if cv2.waitKey(1) & 0xFF == 27:
                print("[i] Exit requested (ESC key)")
                break

    finally:
        print("[i] Cleaning up resources")
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        print("❌ Application terminated with an exception:")
        traceback.print_exc()
        # Exit with non-zero code so editors/CI can detect failure
        import sys
        sys.exit(1)