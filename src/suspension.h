#ifndef SUSPENSION_H
#define SUSPENSION_H

#include <ESP32Servo.h>
#include "config.h"

#define PIN_SUSP_RIGHT 32
#define PIN_SUSP_LEFT  18

Servo suspRight;
Servo suspLeft;

float currentSuspAngle = 90.0;

// === ОФФСЕТЫ ПОДВЕСКИ ===
// Если при угле 90° подвеска стоит криво, подгоните эти значения (например, 5.0, -3.5 и т.д.)
float offsetSuspRight = 0.0; 
float offsetSuspLeft = -23.0;

// Линкуем переменные крестовины из main.cpp
extern bool dpad_up;
extern bool dpad_down;

void initSuspension() {
  // Изолируем таймеры серв (забираем 2 и 3), чтобы не было конфликта с analogWrite моторов
  ESP32PWM::allocateTimer(2);
  ESP32PWM::allocateTimer(3);
  
  suspRight.setPeriodHertz(50);
  suspLeft.setPeriodHertz(50);

  suspRight.attach(PIN_SUSP_RIGHT, 500, 2500);
  suspLeft.attach(PIN_SUSP_LEFT, 500, 2500);
  
  // Стартовое положение: базовая позиция 90° + индивидуальный оффсет
  suspRight.write(constrain(90.0 + offsetSuspRight, 0.0, 180.0));
  suspLeft.write(constrain(90.0 + offsetSuspLeft, 0.0, 180.0));
  
  Serial.println("Подвеска: Инициализирована на пинах 32 (Прав) и 18 (Лев)");
}

void updateSuspension() {
  // Управление с крестовины (D-pad)
  if (dpad_up) {
    currentSuspAngle += 1.5; // Скорость подъема
  }
  if (dpad_down) {
    currentSuspAngle -= 1.5; // Скорость опускания
  }
  
  // Лимиты логического угла подвески
  if (currentSuspAngle > 160.0) currentSuspAngle = 160.0;
  if (currentSuspAngle < 20.0)  currentSuspAngle = 20.0;
  
  // Применяем инверсию и добавляем калибровочные оффсеты
  float finalRight = (180.0 - currentSuspAngle) + offsetSuspRight;
  float finalLeft  = (180.0 - currentSuspAngle) + offsetSuspLeft;
  
  // Защита от выхода за аппаратные пределы сервопривода (0-180)
  suspRight.write(constrain(finalRight, 0.0, 180.0));
  suspLeft.write(constrain(finalLeft, 0.0, 180.0));
}

#endif