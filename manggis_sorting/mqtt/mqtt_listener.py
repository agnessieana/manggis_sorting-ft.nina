import paho.mqtt.client as mqtt
import ssl
import time
import json
import requests
import os
import sys

# =====================================================
# Supaya bisa import config & firebase_client
# =====================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from config.config import (
    MQTT_BROKER,
    MQTT_PORT,
    MQTT_USERNAME,
    MQTT_PASSWORD,
    FIREBASE_URL,
)

# =====================================================
# MQTT CALLBACK
# =====================================================
def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode(errors="ignore")

    # Hanya proses topic status
    if topic.startswith("manggis/status/"):
        device_id = topic.split("/")[-1]

        data = {
            "device_id": device_id,
            "last_seen": int(time.time()),
            "status": "online"
        }

        try:
            # Simpan ke Firebase
            requests.put(
                f"{FIREBASE_URL}/devices/{device_id}.json",
                json=data,
                timeout=3
            )
            print(f"[STATUS] {device_id} updated")

        except Exception as e:
            print("Firebase Error:", e)

# =====================================================
# MAIN
# =====================================================
def main():
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.tls_set(cert_reqs=ssl.CERT_REQUIRED)

    client.on_message = on_message

    print("[MQTT] Connecting to broker...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    client.subscribe("manggis/status/#")
    print("[MQTT] Listening on manggis/status/#")

    client.loop_forever()

if __name__ == "__main__":
    main()
