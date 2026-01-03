#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

/* ================= WIFI ================= */
const char* ssid     = "your wifi ssid";
const char* password = "";

/* ================= MQTT ================= */
const char* mqtt_server = "your mqtt broker address";
const int   mqtt_port   = 8883;
const char* mqtt_user   = "username";
const char* mqtt_pass   = "";

const char* TOPIC_GRADE  = "manggis/grade";
const char* TOPIC_STATUS = "manggis/status/ESP32_Sorter";

/* ================= SERVO PIN ================= */
#define SERVO1_PIN 16
#define SERVO2_PIN 17
#define SERVO3_PIN 18

/* ================= SENSOR PIN ================= */
#define SENSOR1_PIN 32
#define SENSOR2_PIN 33
#define SENSOR3_PIN 25

/* ================= MOTOR PIN (BARU) ================= */
#define MOTOR_IN1 21
#define MOTOR_IN2 22
#define MOTOR_ENA 26   // PWM

/* ================= SERVO PWM ================= */
#define SERVO_PWM_FREQ 50
#define SERVO_PWM_RES  16

/* ================= MOTOR PWM ================= */
#define MOTOR_PWM_FREQ 5000
#define MOTOR_PWM_RES  4
#define MOTOR_SPEED    255   // 🔥 atur kecepatan di sini (0–255)

#define SERVO_HOLD_TIME 5000
#define HEARTBEAT_MS 5000

/* ====== KALIBRASI SERVO ====== */
// MG66R
#define MG66R_MIN 3277
#define MG66R_MAX 6554

// S1500M
#define S1500M_MIN 3400
#define S1500M_MAX 6200

WiFiClientSecure espClient;
PubSubClient client(espClient);

/* ================= STATE ================= */
volatile int activeGrade = 0;
bool servoBusy = false;
unsigned long servoTimer = 0;

/* ================= MOTOR ================= */
void motorForward(int speed) {
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
  ledcWrite(MOTOR_ENA, constrain(speed, 0, 255));
}

/* ================= UTIL ================= */
int servoPin(int grade) {
  if (grade == 1) return SERVO1_PIN;
  if (grade == 2) return SERVO2_PIN;
  if (grade == 3) return SERVO3_PIN;
  return -1;
}

int sensorPin(int grade) {
  if (grade == 1) return SENSOR1_PIN;
  if (grade == 2) return SENSOR2_PIN;
  if (grade == 3) return SENSOR3_PIN;
  return -1;
}

/* ====== KONVERSI DERAJAT ====== */
uint32_t servoMG66R(int deg) {
  deg = constrain(deg, 0, 180);
  return MG66R_MIN + (deg * (MG66R_MAX - MG66R_MIN)) / 150;
}

uint32_t servoS1500M(int deg) {
  deg = constrain(deg, 0, 150);
  return S1500M_MIN + (deg * (S1500M_MAX - S1500M_MIN)) / 150;
}

/* ====== SERVO BUKA ====== */
void setAllServoOpen() {
  ledcWrite(SERVO1_PIN, servoMG66R(0));
  ledcWrite(SERVO2_PIN, servoMG66R(0));
  ledcWrite(SERVO3_PIN, servoS1500M(0));
}

/* ================= MQTT CALLBACK ================= */
void callback(char* topic, byte* payload, unsigned int length) {
  StaticJsonDocument<64> doc;
  if (deserializeJson(doc, payload, length)) return;

  int grade = doc["grade"];
  if (grade < 1 || grade > 3) return;

  activeGrade = grade;
  Serial.print("📩 Grade diterima: ");
  Serial.println(grade);
}

/* ================= SETUP ================= */
void setup() {
  Serial.begin(115200);

  /* SENSOR */
  pinMode(SENSOR1_PIN, INPUT_PULLUP);
  pinMode(SENSOR2_PIN, INPUT_PULLUP);
  pinMode(SENSOR3_PIN, INPUT_PULLUP);

  /* MOTOR */
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);
  ledcAttach(MOTOR_ENA, MOTOR_PWM_FREQ, MOTOR_PWM_RES);
  motorForward(MOTOR_SPEED);   // 🚀 KONVEYOR JALAN + SPEED

  /* SERVO */
  ledcAttach(SERVO1_PIN, SERVO_PWM_FREQ, SERVO_PWM_RES);
  ledcAttach(SERVO2_PIN, SERVO_PWM_FREQ, SERVO_PWM_RES);
  ledcAttach(SERVO3_PIN, SERVO_PWM_FREQ, SERVO_PWM_RES);
  setAllServoOpen();

  /* WIFI */
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n✅ WiFi connected");

  /* MQTT */
  espClient.setInsecure();
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);

  while (!client.connected()) {
    client.connect("ESP32_Sorter", mqtt_user, mqtt_pass);
    delay(1000);
  }

  client.subscribe(TOPIC_GRADE);
  Serial.println("✅ MQTT connected");
}

/* ================= LOOP ================= */
void loop() {
  client.loop();

  /* ===== SENSOR → SERVO ===== */
  if (!servoBusy && activeGrade != 0) {
    int sPin  = sensorPin(activeGrade);
    int svPin = servoPin(activeGrade);

    if (digitalRead(sPin) == LOW) {
      Serial.println("🍈 Buah terdeteksi → SERVO NUTUP");

      if (svPin == SERVO1_PIN || svPin == SERVO2_PIN) {
        ledcWrite(svPin, servoMG66R(100));
      } else {
        ledcWrite(svPin, servoS1500M(100));
      }

      servoBusy = true;
      servoTimer = millis();
    }
  }

  /* ===== SERVO TIMER ===== */
  if (servoBusy && millis() - servoTimer >= SERVO_HOLD_TIME) {
    setAllServoOpen();
    servoBusy = false;
    activeGrade = 0;
    Serial.println("🔓 Servo buka → konveyor tetap jalan");
  }

  /* ===== HEARTBEAT ===== */
  static unsigned long lastHb = 0;
  if (millis() - lastHb > HEARTBEAT_MS) {
    client.publish(TOPIC_STATUS, "{\"status\":\"online\"}");
    lastHb = millis();
  }
}