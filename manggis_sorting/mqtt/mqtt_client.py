import paho.mqtt.client as mqtt
import ssl
import json

class MQTTClient:
    def __init__(self, broker, port, username, password):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(username, password)
        self.client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
        self.client.connect(broker, port, 60)
        self.client.loop_start()

    def publish_grade(self, topic, grade):
        payload = json.dumps({"grade": int(grade)})
        self.client.publish(topic, payload)
