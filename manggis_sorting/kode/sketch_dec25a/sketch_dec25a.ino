#include <WiFi.h>
#include <HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ESP32Servo.h>

/* ================= WIFI ================= */
const char* WIFI_SSID = "Mabes";
const char* WIFI_PASS = "sukasukagw";

/* ================= FIREBASE ================= */
const char* FIREBASE_GRADE_URL =
"https://gradding-mangosteen-default-rtdb.asia-southeast1.firebasedatabase.app/grading/grade.json";

/* ================= SENSOR ================= */
#define SENSOR_1 32
#define SENSOR_2 33
#define SENSOR_3 25

/* ================= SERVO ================= */
#define SERVO_1 26
#define SERVO_2 27
#define SERVO_3 14

/* ================= MOTOR L298N ================= */
#define MOTOR_EN  13   // ENA (PWM)
#define MOTOR_IN1 12
#define MOTOR_IN2 4

/* ================= MANUAL SPEED ================= */
#define MOTOR_SPEED 180   // <<< ATUR KECEPATAN CONVEYOR (0–255)

/* ================= OBJECT ================= */
Servo servo1, servo2, servo3;
WiFiClientSecure client;

/* ================= STATE ================= */
int currentGrade = -1;

bool lastSensor1 = LOW;
bool lastSensor2 = LOW;
bool lastSensor3 = LOW;

unsigned long lastFirebaseRead = 0;
unsigned long servoTimer = 0;
bool servoActive = false;

/* ================= WIFI CONNECT ================= */
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected");
}

/* ================= MOTOR ================= */
void motorStart() {
  digitalWrite(MOTOR_IN1, HIGH);
  digitalWrite(MOTOR_IN2, LOW);
  analogWrite(MOTOR_EN, MOTOR_SPEED);
}

/* ================= FIREBASE GET ================= */
void fetchGrade() {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient https;
  client.setInsecure(); // wajib untuk HTTPS Firebase

  if (https.begin(client, FIREBASE_GRADE_URL)) {
    if (https.GET() == HTTP_CODE_OK) {
      currentGrade = https.getString().toInt();
    }
    https.end();
  }
}

/* ================= SERVO ================= */
void activateServo(Servo &srv) {
  servoActive = true;
  servoTimer = millis();
  srv.write(90);
}

/* ================= SETUP ================= */
void setup() {
  Serial.begin(115200);

  /* Sensor */
  pinMode(SENSOR_1, INPUT);
  pinMode(SENSOR_2, INPUT);
  pinMode(SENSOR_3, INPUT);

  /* Motor */
  pinMode(MOTOR_EN, OUTPUT);
  pinMode(MOTOR_IN1, OUTPUT);
  pinMode(MOTOR_IN2, OUTPUT);

  /* Servo */
  servo1.attach(SERVO_1);
  servo2.attach(SERVO_2);
  servo3.attach(SERVO_3);

  servo1.write(0);
  servo2.write(0);
  servo3.write(0);

  connectWiFi();

  /* 🚀 CONVEYOR LANGSUNG MENYALA */
  motorStart();
}

/* ================= LOOP ================= */
void loop() {
  unsigned long now = millis();

  /* === Ambil grade dari Firebase tiap 1 detik === */
  if (now - lastFirebaseRead > 1000) {
    fetchGrade();
    lastFirebaseRead = now;

    Serial.print("Grade: ");
    Serial.println(currentGrade);
  }

  bool s1 = digitalRead(SENSOR_1);
  bool s2 = digitalRead(SENSOR_2);
  bool s3 = digitalRead(SENSOR_3);

  /* === SORTING LOGIC === */
  if (!servoActive) {
    if (currentGrade == 1 && s1 == HIGH && lastSensor1 == LOW) {
      Serial.println("Sortir Grade A");
      activateServo(servo1);
      currentGrade = -1;
    }
    else if (currentGrade == 2 && s2 == HIGH && lastSensor2 == LOW) {
      Serial.println("Sortir Grade B");
      activateServo(servo2);
      currentGrade = -1;
    }
    else if (currentGrade == 3 && s3 == HIGH && lastSensor3 == LOW) {
      Serial.println("Sortir Grade C");
      activateServo(servo3);
      currentGrade = -1;
    }
  }

  /* === SERVO OFF OTOMATIS === */
  if (servoActive && now - servoTimer > 400) {
    servo1.write(0);
    servo2.write(0);
    servo3.write(0);
    servoActive = false;
  }

  /* Simpan status sensor */
  lastSensor1 = s1;
  lastSensor2 = s2;
  lastSensor3 = s3;
}
 