#include <WiFi.h>
#include <WiFiUdp.h>
#include "config.h"
#include "motors.h"
#include "servos.h"
#include "suspension.h"
#include <ESP32Servo.h>

WiFiUDP udp;
uint8_t packetBuffer[PACKET_SIZE];

unsigned long lastPacketTime = 0;
unsigned long lastButtonPress = 0;
const uint32_t DEBOUNCE_DELAY = 200;

bool a_button, b_button, x_button, y_button, right_button, left_button;
bool dpad_up, dpad_right, dpad_left, dpad_down;
uint8_t l_trigger = 0, r_trigger = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.mode(WIFI_STA);
  WiFi.setTxPower(WIFI_POWER_19_5dBm);
  WiFi.begin(ssid, password);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWi-Fi подключен! IP: " + WiFi.localIP().toString());
  } else {
    Serial.println("\nWi-Fi не подключен.");
  }

  initMotors();
  initServos();
  initSuspension(); // Инициализация подвески

  udp.begin(UDP_PORT);
  Serial.println("UDP приемник запущен.");
  lastPacketTime = millis();
}

void unpackButtons(uint8_t buttonByte1, uint8_t buttonByte2) {
  left_button  = (buttonByte1 & (1 << 0)) != 0;
  right_button = (buttonByte1 & (1 << 1)) != 0;
  a_button     = (buttonByte1 & (1 << 4)) != 0;
  b_button     = (buttonByte1 & (1 << 5)) != 0;
  x_button     = (buttonByte1 & (1 << 6)) != 0;
  y_button     = (buttonByte1 & (1 << 7)) != 0;

  dpad_up      = (buttonByte2 & (1 << 0)) != 0;
  dpad_right   = (buttonByte2 & (1 << 1)) != 0;
  dpad_left    = (buttonByte2 & (1 << 2)) != 0;
  dpad_down    = (buttonByte2 & (1 << 3)) != 0;
}

void loop() {
  bool hasNewData = false;

  while (udp.parsePacket() == PACKET_SIZE) {
    udp.read(packetBuffer, PACKET_SIZE);
    hasNewData = true;
  }

  if (hasNewData) {
    if (packetBuffer[0] == START_BYTE) {
      uint8_t calculatedCRC = 0;
      for (int i = 1; i < PACKET_SIZE - 1; i++) {
        calculatedCRC += packetBuffer[i];
      }

      if (calculatedCRC == packetBuffer[PACKET_SIZE - 1]) {
        unpackButtons(packetBuffer[5], packetBuffer[6]);

        l_trigger = packetBuffer[7];
        r_trigger = packetBuffer[8];

        setMotors(packetBuffer[1], packetBuffer[2]);

        uint8_t rightStickXRaw = packetBuffer[3];
        uint8_t rightStickYRaw = packetBuffer[4];

        if (left_button) {
          updateServo4Position(rightStickXRaw);
          updateArmKinematics(rightStickYRaw, 1);
        } else {
          updateServoPosition(rightStickXRaw);
          updateArmKinematics(rightStickYRaw, 0);
        }

        updateGripper3(l_trigger, r_trigger);
        
        // ВЫЗОВ УПРАВЛЕНИЯ ПОДВЕСКОЙ
        updateSuspension();

        if (b_button && (millis() - lastButtonPress > DEBOUNCE_DELAY)) {
          lastButtonPress = millis();
          toggleManipulatorState();
        }

        lastPacketTime = millis();
      } else {
        Serial.println("CRC ошибка!");
      }
    }
  }

  if (millis() - lastPacketTime > FAILSAFE_TIMEOUT) {
    setMotors(128, 128);
  }
}