#ifndef SERVOS_H
#define SERVOS_H

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "config.h"

// Объявляем объект шилда (физическое создание)
Adafruit_PWMServoDriver pwmShield = Adafruit_PWMServoDriver(PCA9685_ADDR);

// === КАЛИБРОВКА ДЛЯ СЕРВ ПРИВОДОВ ===
#define SERVO_MIN_PWM  102   // Соответствует 0°
#define SERVO_MAX_PWM  512   // Соответствует максимуму (240°)

// === ПЕРЕМЕННЫЕ ЛОГИЧЕСКИХ УГЛОВ ===
float currentServoAngle = 110.0;    // Серва 1: Поворотная основа (Временно ограничена 65-155°)
float currentLink1Angle = 25.0;     // Серва 2: Первая колонна (канал 1)
float targetLink2Angle  = 260.0;    // Серва 3: Вторая колонна (канал 2)

// Хват клешни переезжает на 3-й канал шилда PCA9685
float servo3_gripper    = 120.0;    // Серва Хвата: канал 3 (Управляется через LT/RT)
float servo4_angle      = 120.0;    // Серва 4: Резерв / доп. ось (канал 4)

// Старые переменные навесного оборудования
int gripper_angle = 90;          
int rotate_grip_angle = 90;      
int rotate_down_angle = 135;     

// Динамические оффсеты для точной калибровки
float offsetServo0 = 0.0;
float offsetServo1 = 0.0;
float offsetServo2 = 0.0;
float offsetServo3 = 0.0; // Для хвата
float offsetServo4 = 0.0;

bool isCalibrationMode = false;
bool manipulatorState = false;   

// Линкуем переменные времени дебаунса из главного ino файла
extern unsigned long lastButtonPress;
extern const uint32_t DEBOUNCE_DELAY;

const int STICK_DEADZONE = 15; 
unsigned long lastDebugTime = 0;

void servoWrite240(uint8_t channel, int angle) {
  angle = constrain(angle, 0, 240);
  uint16_t pulse = map(angle, 0, 240, SERVO_MIN_PWM, SERVO_MAX_PWM);
  pwmShield.setPWM(channel, 0, pulse);
}

void servoWrite180(uint8_t channel, int angle) {
  angle = constrain(angle, 0, 180);
  uint16_t pulse = map(angle, 0, 180, SERVO_MIN_PWM, SERVO_MAX_PWM);
  pwmShield.setPWM(channel, 0, pulse);
}

void writeServoAngle(uint8_t servoNum, float angle, float offset, float minAngle, float maxAngle) {
  float finalAngle = angle + offset;
  if (finalAngle > maxAngle) finalAngle = maxAngle;
  if (finalAngle < minAngle) finalAngle = minAngle;
  
  // Каналы 0, 1, 2, 3, 4 работают по логике 240 градусов
  if (servoNum == TEST_SERVO_NUM || servoNum == LINK1_SERVO_NUM || servoNum == 2 || servoNum == 3 || servoNum == 4) {  
    servoWrite240(servoNum, int(finalAngle));
  } else {  
    servoWrite180(servoNum, int(finalAngle));
  }
}

void initServos() {
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN); 
  pwmShield.begin();
  pwmShield.setOscillatorFrequency(27000000);
  pwmShield.setPWMFreq(50); 
  
  // Стартовые позиции с учетом временного лимита для Сервы 1
  if (currentServoAngle > 155.0) currentServoAngle = 155.0;
  if (currentServoAngle < 65.0)  currentServoAngle = 65.0;
  writeServoAngle(TEST_SERVO_NUM, currentServoAngle, offsetServo0, 65.0, 155.0);
  
  float finalLink1Angle = currentLink1Angle;
  if (LINK1_INVERTED) finalLink1Angle = LINK1_MAX_ANGLE - currentLink1Angle;
  writeServoAngle(LINK1_SERVO_NUM, finalLink1Angle, offsetServo1, LINK1_MIN_ANGLE, LINK1_MAX_ANGLE);
  
  float jointAngle = targetLink2Angle - currentLink1Angle;
  float correctedJointAngle = 1.5 * jointAngle - 90.0;
  float finalLink2Angle = correctedJointAngle;
  if (LINK2_INVERTED) finalLink2Angle = 180.0 - correctedJointAngle;
  writeServoAngle(2, finalLink2Angle, offsetServo2, LINK2_MIN_ANGLE, LINK2_MAX_ANGLE);
  
  // Инициализация Хвата (канал 3) и Сервы 4 (канал 4)
  writeServoAngle(3, servo3_gripper, offsetServo3, 115.0, 200.0);
  writeServoAngle(4, servo4_angle, offsetServo4, 115.0, 200.0);

  servoWrite180(13, rotate_grip_angle);  
  servoWrite180(12, gripper_angle);      
  
  Serial.println("✓ Сервоприводы инициализированы. Хват на канале 3.");
}


// Серва 1: Поворот основания с ВРЕМЕННЫМ ОГРАНИЧЕНИЕМ 65..155
void updateServoPosition(uint8_t stickRaw) {
  if (isCalibrationMode) return;
  int deviation = int(stickRaw) - 128;
  if (abs(deviation) < STICK_DEADZONE) return; 
  
  currentServoAngle += float(deviation) / 55.0;
  if (currentServoAngle > 155.0) currentServoAngle = 155.0;
  if (currentServoAngle < 65.0)  currentServoAngle = 65.0;
}

// Управление Хватом на 3-м пине Шилда с помощью LT и R
void updateGripper3(uint8_t lTrigger, uint8_t rTrigger) {
  if (isCalibrationMode) return;
  
  if (lTrigger > 2) {
    servo3_gripper += 2.5; // а точно ли??? 
  }
  if (rTrigger > 2) {
    servo3_gripper -= 2.5; 
  }
  
  // Безопасные лимиты для твоей конструкции хвата 
  if (servo3_gripper > 200.0) servo3_gripper = 200.0;
  if (servo3_gripper < 115.0) servo3_gripper = 115.0;
}

// Резервная Серва 4 на канале 4
void updateServo4Position(uint8_t stickRaw) {
  if (isCalibrationMode) return;
  int deviation = int(stickRaw) - 128;
  if (abs(deviation) < STICK_DEADZONE) return;
  
  servo4_angle += float(deviation) / 55.0;
  if (servo4_angle > 240.0) servo4_angle = 240.0;
  if (servo4_angle < 0.0)   servo4_angle = 0.0;
}

void updateArmKinematics(uint8_t stickYRaw, uint8_t lbPressed) {
  if (!isCalibrationMode) {
    int deviation = 128 - int(stickYRaw); 
    if (abs(deviation) >= STICK_DEADZONE) {
      float speedFactor = float(deviation) / 55.0; 

      if (lbPressed == 1) {
        targetLink2Angle -= speedFactor; 
        // Защита переменной цели Сервы 3 под её новый максимум
        if (targetLink2Angle > LINK2_MAX_ANGLE) targetLink2Angle = LINK2_MAX_ANGLE;
        if (targetLink2Angle < LINK2_MIN_ANGLE) targetLink2Angle = LINK2_MIN_ANGLE;
      } 
      else {
        currentLink1Angle += speedFactor;
        if (currentLink1Angle > LINK1_MAX_ANGLE) currentLink1Angle = LINK1_MAX_ANGLE;
        if (currentLink1Angle < LINK1_MIN_ANGLE) currentLink1Angle = LINK1_MIN_ANGLE;
      }
    }
  }

  // 1. Финальный расчет угла для Сервы 1 (Поворотное основание, индекс 0)
  float outAngleServo0 = currentServoAngle + offsetServo0;
  if (outAngleServo0 > 155.0) outAngleServo0 = 155.0;
  if (outAngleServo0 < 65.0)  outAngleServo0 = 65.0;

  // 2. Финальный расчет угла для Сервы 2 (Первая колонна, индекс 1)
  float logicAngle1 = currentLink1Angle;
  if (LINK1_INVERTED) logicAngle1 = LINK1_MAX_ANGLE - currentLink1Angle;
  float outAngleServo1 = logicAngle1 + offsetServo1;

  // 3. Финальный расчет угла для Сервы 3 (Вторая колонна, индекс 2)
  float jointAngle = targetLink2Angle - currentLink1Angle;
  float correctedJointAngle = 1.5 * jointAngle - 90.0;
  
  // Жесткое ограничение расчетного угла Сервы 3 под новые физические лимиты (0...200)
  if (correctedJointAngle > LINK2_MAX_ANGLE) correctedJointAngle = LINK2_MAX_ANGLE;
  if (correctedJointAngle < LINK2_MIN_ANGLE) correctedJointAngle = LINK2_MIN_ANGLE;

  float logicAngle2 = correctedJointAngle;
  if (LINK2_INVERTED) logicAngle2 = 180.0 - correctedJointAngle; 
  float outAngleServo2 = logicAngle2 + offsetServo2;

  // 4. Финальный расчет для хвата (индекс 3) и доп. оси (индекс 4)
  float outAngleServo3 = servo3_gripper + offsetServo3;
  float outAngleServo4 = servo4_angle + offsetServo4;

  // Безопасность наклона кисти из старой логики
  if (((rotate_down_angle > 155) || (rotate_down_angle < 115)) && (outAngleServo1 <= 120)) {
    outAngleServo1 = 122;  
  }

  // ОТПРАВКА НА ШИЛД PCA9685 с новыми скорректированными лимитами
  writeServoAngle(TEST_SERVO_NUM, outAngleServo0, 0.0, 65.0, 155.0);          // Серва 1 (канал 0)
  writeServoAngle(LINK1_SERVO_NUM, outAngleServo1, 0.0, LINK1_MIN_ANGLE, LINK1_MAX_ANGLE); // Серва 2 (канал 1) -> теперь до 220.0
  writeServoAngle(LINK2_SERVO_NUM, outAngleServo2, 0.0, LINK2_MIN_ANGLE, LINK2_MAX_ANGLE); // Серва 3 (канал 2) -> теперь жестко до 200.0
  writeServoAngle(3, outAngleServo3, 0.0, 115.0, 200.0);                      // Хват (канал 3)
  writeServoAngle(4, outAngleServo4, 0.0, 0.0, 240.0);                       // Резерв (канал 4)

  if (millis() - lastDebugTime > 250) {
    lastDebugTime = millis();
    Serial.printf("S1: %.1f° | S2 (до 220): %.1f° | S3 (до 200): %.1f° | Хват: %.1f°\n", 
                  outAngleServo0, outAngleServo1, outAngleServo2, outAngleServo3);
  }
}

void toggleManipulatorState() {
  manipulatorState = !manipulatorState;
  if (manipulatorState) {
    currentLink1Angle = 240; targetLink2Angle = 185; servo3_gripper = 60;
  } else {
    currentLink1Angle = 175; targetLink2Angle = 185; servo3_gripper = 120;
  }
}

void updateAllServos() {
  updateArmKinematics(128, 0);
}
#endif