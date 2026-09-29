#ifndef MOTORS_H
#define MOTORS_H

#include <Arduino.h>
#include "config.h"

#define PWM_FREQ     20000
#define PWM_RES      8
#define LEDC_CH_LEFT  0
#define LEDC_CH_RIGHT 1

bool isInverted = false;
int  deadZone   = 15;

void initMotors() {
  ledcSetup(LEDC_CH_LEFT,  PWM_FREQ, PWM_RES);
  ledcSetup(LEDC_CH_RIGHT, PWM_FREQ, PWM_RES);
  ledcAttachPin(LEFT_MOTOR_PWM,  LEDC_CH_LEFT);
  ledcAttachPin(RIGHT_MOTOR_PWM, LEDC_CH_RIGHT);

  pinMode(LEFT_MOTOR_INA,  OUTPUT);
  pinMode(LEFT_MOTOR_INB,  OUTPUT);
  pinMode(RIGHT_MOTOR_INA, OUTPUT);
  pinMode(RIGHT_MOTOR_INB, OUTPUT);

  ledcWrite(LEDC_CH_LEFT,  0);
  ledcWrite(LEDC_CH_RIGHT, 0);
  Serial.println("✓ Моторы инициализированы (LEDC).");
}

void setMotors(uint8_t leftRaw, uint8_t rightRaw) {
  int leftSpeed  = (int(leftRaw)  - 128) * 2;
  int rightSpeed = (int(rightRaw) - 128) * 2;

  leftSpeed  = constrain(leftSpeed,  -255, 255);
  rightSpeed = constrain(rightSpeed, -255, 255);

  if (abs(leftSpeed)  < deadZone) leftSpeed  = 0;
  if (abs(rightSpeed) < deadZone) rightSpeed = 0;

  if (isInverted) {
    leftSpeed  = -leftSpeed;
    rightSpeed = -rightSpeed;
  }

  if (leftSpeed > 0) {
    digitalWrite(LEFT_MOTOR_INA, HIGH);
    digitalWrite(LEFT_MOTOR_INB, LOW);
    ledcWrite(LEDC_CH_LEFT, leftSpeed);
  } else if (leftSpeed < 0) {
    digitalWrite(LEFT_MOTOR_INA, LOW);
    digitalWrite(LEFT_MOTOR_INB, HIGH);
    ledcWrite(LEDC_CH_LEFT, -leftSpeed);
  } else {
    digitalWrite(LEFT_MOTOR_INA, LOW);
    digitalWrite(LEFT_MOTOR_INB, LOW);
    ledcWrite(LEDC_CH_LEFT, 0);
  }

  if (rightSpeed > 0) {
    digitalWrite(RIGHT_MOTOR_INA, HIGH);
    digitalWrite(RIGHT_MOTOR_INB, LOW);
    ledcWrite(LEDC_CH_RIGHT, rightSpeed);
  } else if (rightSpeed < 0) {
    digitalWrite(RIGHT_MOTOR_INA, LOW);
    digitalWrite(RIGHT_MOTOR_INB, HIGH);
    ledcWrite(LEDC_CH_RIGHT, -rightSpeed);
  } else {
    digitalWrite(RIGHT_MOTOR_INA, LOW);
    digitalWrite(RIGHT_MOTOR_INB, LOW);
    ledcWrite(LEDC_CH_RIGHT, 0);
  }
}

#endif