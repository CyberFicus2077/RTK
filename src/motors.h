
// motors.h
#ifndef MOTORS_H
#define MOTORS_H

#include <Arduino.h>
#include "config.h"

// Функция инициализации моторов
void initMotors() {
  pinMode(LEFT_MOTOR_PWM, OUTPUT);
  pinMode(LEFT_MOTOR_INA, OUTPUT);
  pinMode(LEFT_MOTOR_INB, OUTPUT);

  pinMode(RIGHT_MOTOR_PWM, OUTPUT);
  pinMode(RIGHT_MOTOR_INA, OUTPUT);
  pinMode(RIGHT_MOTOR_INB, OUTPUT);
}

bool isInverted = true;
int deadZone = 15;

// Функция управления скоростью
// Скорость принимает значения от 0 до 255, где 0 - максимальный назад, 128 - стоп, 255 - максимальный вперёд
void setMotors(uint8_t leftRaw, uint8_t rightRaw) {

  // Перевод шкалы [0; 255] в шкалу [-255; 255]
  int leftSpeed = (int(leftRaw) - 128) * 2;
  int rightSpeed = (int(rightRaw) - 128) * 2;

  // Защита краев (чтобы не вылететь за пределы ШИМ)
  if (leftSpeed > 255) leftSpeed = 255;
  if (leftSpeed < -255) leftSpeed = -255;
  if (rightSpeed > 255) rightSpeed = 255;
  if (rightSpeed < -255) rightSpeed = -255;

  // Мёртвая зона
  if (abs(leftSpeed) < deadZone) leftSpeed = 0;
  if (abs(rightSpeed) < deadZone) rightSpeed = 0;


  if (isInverted) {
    leftSpeed = -leftSpeed;
    rightSpeed = -rightSpeed;
  }

  // Левый борт
  if (leftSpeed > 0) {

    digitalWrite(LEFT_MOTOR_INA, HIGH);
    digitalWrite(LEFT_MOTOR_INB, LOW);
    analogWrite(LEFT_MOTOR_PWM, leftSpeed);
  } 
  else if (leftSpeed < 0) {

    digitalWrite(LEFT_MOTOR_INA, LOW);
    digitalWrite(LEFT_MOTOR_INB, HIGH);
    analogWrite(LEFT_MOTOR_PWM, -leftSpeed);
  }
  else {
    digitalWrite(LEFT_MOTOR_INA, LOW);
    digitalWrite(LEFT_MOTOR_INB, LOW);
    analogWrite(LEFT_MOTOR_PWM, 0);
  }

  // Правый борт
  if (rightSpeed > 0) {

    digitalWrite(RIGHT_MOTOR_INA, HIGH);
    digitalWrite(RIGHT_MOTOR_INB, LOW);
    analogWrite(RIGHT_MOTOR_PWM, rightSpeed);
  } 
  else if (rightSpeed < 0) {

    digitalWrite(RIGHT_MOTOR_INA, LOW);
    digitalWrite(RIGHT_MOTOR_INB, HIGH);
    analogWrite(RIGHT_MOTOR_PWM, -rightSpeed);
  }
  else {
    digitalWrite(RIGHT_MOTOR_INA, LOW);
    digitalWrite(RIGHT_MOTOR_INB, LOW);
    analogWrite(RIGHT_MOTOR_PWM, 0);
  }
}

#endif