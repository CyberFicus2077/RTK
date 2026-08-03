
//main.cpp
#include <WiFi.h>
#include <WiFiUdp.h>
#include "config.h"
#include "motors.h"
#include "servos.h"
#include "suspension.h"

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
  initSuspension();

  udp.begin(UDP_PORT);
  Serial.println("UDP приемник запущен.");

  lastPacketTime = millis();
}

// Распаковка битовой маски в соответствии со структурой Python-пакета
void unpackButtons(uint8_t buttonByte1, uint8_t buttonByte2) {
  // Байт 5 (buttonByte1)
  left_button  = (buttonByte1 & (1 << 0)) != 0; // 1-й бит: LB
  right_button = (buttonByte1 & (1 << 1)) != 0; // 2-й бит: RB
  l_trigger    = (buttonByte1 & (1 << 2)) ? 255 : 0; // 3-й бит: LT
  r_trigger    = (buttonByte1 & (1 << 3)) ? 255 : 0; // 4-й бит: RT
  a_button     = (buttonByte1 & (1 << 4)) != 0; // 5-й бит: A
  b_button     = (buttonByte1 & (1 << 5)) != 0; // 6-й бит: B
  x_button     = (buttonByte1 & (1 << 6)) != 0; // 7-й бит: X
  y_button     = (buttonByte1 & (1 << 7)) != 0; // 8-й бит: Y
  
  // Байт 6 (buttonByte2) - D-pad
  dpad_up      = (buttonByte2 & (1 << 0)) != 0;
  dpad_right   = (buttonByte2 & (1 << 1)) != 0;
  dpad_left    = (buttonByte2 & (1 << 2)) != 0;
  dpad_down    = (buttonByte2 & (1 << 3)) != 0;
}

void loop() {
  bool hasNewData = false;

  // Очистка и чтение буфера пакетов UDP
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
        
        // Извлекаем состояния кнопок
        unpackButtons(packetBuffer[5], packetBuffer[6]);
        
        // 1. Движение гусениц
        uint8_t leftMotorRaw  = packetBuffer[1];
        uint8_t rightMotorRaw = packetBuffer[2];  
        setMotors(leftMotorRaw, rightMotorRaw);

        // 2. Оси правого стика
        uint8_t rightStickXRaw = packetBuffer[3];
        uint8_t rightStickYRaw = packetBuffer[4];

        // Распределение задач правого стика в зависимости от зажатия LB
        if (left_button) { 
          updateServo4Position(rightStickXRaw);        // Стик X -> Резерв серва 4 (пины шилда 4)
          updateArmKinematics(rightStickYRaw, 1);      // Стик Y -> Колонна 2
        } else {
          updateServoPosition(rightStickXRaw);         // Стик X -> Основание Серва 1 (65°-155°)
          updateArmKinematics(rightStickYRaw, 0);      // Стик Y -> Колонна 1
        }

        // 3. УПРАВЛЕНИЕ ХВАТОМ НА СЕРВЕ 3 (3-й пин) через LT и RT
        updateGripper3(l_trigger, r_trigger);
        
        // 4. Переключение пресетов по кнопке B
        if (b_button && (millis() - lastButtonPress > DEBOUNCE_DELAY)) {
          lastButtonPress = millis();
          toggleManipulatorState();
        }

        lastPacketTime = millis(); 

      } else {
        Serial.println("Ошибка: Контрольная сумма CRC не совпала!");
      }
    }
  }

  if (millis() - lastPacketTime > FAILSAFE_TIMEOUT) {
    setMotors(128, 128); // Стоп при потере сигнала
  }
}