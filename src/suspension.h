#ifndef SUSPENSION_H
#define SUSPENSION_H

#include <Adafruit_PWMServoDriver.h>
#include "config.h"

extern Adafruit_PWMServoDriver pwmShield;

void writeSuspensionAngle(uint8_t servoNum, float angle) {
  if (angle > SERVO_MAX_ANGLE) angle = SERVO_MAX_ANGLE;
  if (angle < 0.0) angle = 0.0;
  int pwmPulse = map(int(angle), 0, int(SERVO_MAX_ANGLE), SERVOMIN, SERVOMAX);
  pwmShield.setPWM(servoNum, 0, pwmPulse);
}

void initSuspension() {
  writeSuspensionAngle(SUSPENSION_L_NUM, 80.0);
  writeSuspensionAngle(SUSPENSION_R_NUM, 70.0);
  Serial.println("Подвеска инициализирована.");
}

#endif