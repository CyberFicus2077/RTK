#ifndef SERVOS_H
#define SERVOS_H

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>
#include "config.h"

Adafruit_PWMServoDriver pwmShield = Adafruit_PWMServoDriver(PCA9685_ADDR);

#define SERVO_MIN_PWM  102
#define SERVO_MAX_PWM  512

// === ПЕРЕМЕННЫЕ ===
float currentServoAngle = 120.0;
float currentLink1Angle = 25.0;
float targetLink2Angle  = 260.0;

float servo4_rotation = 120.0;   // Вращение хвата
float servo5_gripper  = 50.0;    // Сжатие/разжатие

float offsetServo0 = 0.0;
float offsetServo1 = 0.0;
float offsetServo2 = 0.0;
float offsetServo3 = 0.0;
float offsetServo4 = 0.0;

bool isCalibrationMode = false;
bool manipulatorState = false;

extern unsigned long lastButtonPress;
extern const uint32_t DEBOUNCE_DELAY;

const int STICK_DEADZONE = 15;
unsigned long lastDebugTime = 0;

// === БАЗОВЫЕ ФУНКЦИИ ===
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

void writeServoAngle(uint8_t servoNum, float angle, float offset,
                     float minAngle, float maxAngle) {
  float finalAngle = constrain(angle + offset, minAngle, maxAngle);
  if (servoNum <= 3) servoWrite240(servoNum, int(finalAngle));
  else               servoWrite180(servoNum, int(finalAngle));
}

void initServos() {
  Wire.begin(I2C_SDA_PIN, I2C_SCL_PIN);
  pwmShield.begin();
  pwmShield.setOscillatorFrequency(27000000);
  pwmShield.setPWMFreq(50);

  writeServoAngle(TEST_SERVO_NUM, currentServoAngle, offsetServo0, 0.0, 240.0);

  float finalLink1Angle = currentLink1Angle;
  if (LINK1_INVERTED) finalLink1Angle = LINK1_MAX_ANGLE - currentLink1Angle;
  writeServoAngle(LINK1_SERVO_NUM, finalLink1Angle, offsetServo1, LINK1_MIN_ANGLE, LINK1_MAX_ANGLE);

  float jointAngle = targetLink2Angle - currentLink1Angle;
  float correctedJointAngle = 1.5 * jointAngle - 90.0;
  float finalLink2Angle = correctedJointAngle;
  if (LINK2_INVERTED) finalLink2Angle = 180.0 - correctedJointAngle;
  writeServoAngle(LINK2_SERVO_NUM, finalLink2Angle, offsetServo2, LINK2_MIN_ANGLE, LINK2_MAX_ANGLE);

  writeServoAngle(ROTATE_GRIP_NUM, servo4_rotation, offsetServo3, 0.0, 240.0);
  writeServoAngle(GRIPPER_SERVO_NUM, servo5_gripper, offsetServo4, GRIPPER_MIN, GRIPPER_MAX);

  Serial.println("✓ Сервы готовы.");
}

// === ПОВОРОТ ОСНОВАНИЯ (скорость из config.h) ===
void updateServoPosition(uint8_t stickRaw) {
  if (isCalibrationMode) return;
  int deviation = int(stickRaw) - 128;
  if (abs(deviation) < STICK_DEADZONE) return;

  currentServoAngle += float(deviation) / BASE_SPEED_DIV;
  currentServoAngle = constrain(currentServoAngle, 0.0, 240.0);
}

// === ВРАЩЕНИЕ ХВАТА (скорость из config.h) ===
void updateServo4Position(uint8_t stickRaw) {
  if (isCalibrationMode) return;
  int deviation = int(stickRaw) - 128;
  if (abs(deviation) < STICK_DEADZONE) return;

  servo4_rotation -= float(deviation) / ROTATE_SPEED_DIV;
  servo4_rotation = constrain(servo4_rotation, 0.0, 240.0);
}

// === ХВАТ (плавно, скорость из config.h) ===
void updateGripper3(uint8_t lTrigger, uint8_t rTrigger) {
  if (isCalibrationMode) return;

  if (lTrigger < 20) lTrigger = 0;
  if (rTrigger < 20) rTrigger = 0;

  float speedL = (lTrigger / 255.0) * GRIPPER_SPEED;
  float speedR = (rTrigger / 255.0) * GRIPPER_SPEED;

  servo5_gripper += speedL;
  servo5_gripper -= speedR;

  servo5_gripper = constrain(servo5_gripper, GRIPPER_MIN, GRIPPER_MAX);
}

// === КИНЕМАТИКА КОЛОНН (скорость из config.h) ===
void updateArmKinematics(uint8_t stickYRaw, uint8_t lbPressed) {
  if (!isCalibrationMode) {
    int deviation = 128 - int(stickYRaw);
    if (abs(deviation) >= STICK_DEADZONE) {
      float speedFactor = float(deviation) / ARM_SPEED_DIV;

      if (lbPressed == 1) {
        targetLink2Angle -= speedFactor;
        targetLink2Angle = constrain(targetLink2Angle, -200.0, 400.0);
      }
      else {
        currentLink1Angle += speedFactor;
        currentLink1Angle = constrain(currentLink1Angle, LINK1_MIN_ANGLE, LINK1_MAX_ANGLE);
      }
    }
  }

  float outAngleServo0 = constrain(currentServoAngle + offsetServo0, 0.0, 240.0);

  float logicAngle1 = currentLink1Angle;
  if (LINK1_INVERTED) logicAngle1 = LINK1_MAX_ANGLE - currentLink1Angle;
  float outAngleServo1 = logicAngle1 + offsetServo1;

  float jointAngle = targetLink2Angle - currentLink1Angle;
  float correctedJointAngle = 1.5 * jointAngle - 90.0;
  correctedJointAngle = constrain(correctedJointAngle, LINK2_MIN_ANGLE, LINK2_MAX_ANGLE);

  float logicAngle2 = correctedJointAngle;
  if (LINK2_INVERTED) logicAngle2 = 180.0 - correctedJointAngle;
  float outAngleServo2 = logicAngle2 + offsetServo2;

  float outAngleServo3 = servo4_rotation + offsetServo3;
  float outAngleServo4 = servo5_gripper + offsetServo4;

  writeServoAngle(TEST_SERVO_NUM, outAngleServo0, 0.0, 0.0, 240.0);
  writeServoAngle(LINK1_SERVO_NUM, outAngleServo1, 0.0, LINK1_MIN_ANGLE, LINK1_MAX_ANGLE);
  writeServoAngle(LINK2_SERVO_NUM, outAngleServo2, 0.0, LINK2_MIN_ANGLE, LINK2_MAX_ANGLE);
  writeServoAngle(ROTATE_GRIP_NUM, outAngleServo3, 0.0, 0.0, 240.0);
  writeServoAngle(GRIPPER_SERVO_NUM, outAngleServo4, 0.0, GRIPPER_MIN, GRIPPER_MAX);

  if (millis() - lastDebugTime > 250) {
    lastDebugTime = millis();
    Serial.printf("Base: %.1f | L1: %.1f | L2: %.1f | Rot: %.1f | Grip: %.1f\n",
                  outAngleServo0, outAngleServo1, outAngleServo2,
                  outAngleServo3, outAngleServo4);
  }
}

void toggleManipulatorState() {
  manipulatorState = !manipulatorState;
  if (manipulatorState) {
    currentLink1Angle = 240;
    targetLink2Angle = 185;
    servo5_gripper = 0;
  } else {
    currentLink1Angle = 175;
    targetLink2Angle = 185;
    servo5_gripper = 100;
  }
}

void updateAllServos() {
  updateArmKinematics(128, 0);
}

#endif