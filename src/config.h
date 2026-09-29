#ifndef CONFIG_H
#define CONFIG_H

const char* ssid = "K-lab-Robot";
const char* password = "allhailklab";
#define UDP_PORT 99

#define START_BYTE 0xAA
#define PACKET_SIZE 10
#define FAILSAFE_TIMEOUT 500

// === МОТОРЫ ===
#define LEFT_MOTOR_PWM  26
#define LEFT_MOTOR_INA  33
#define LEFT_MOTOR_INB  25
#define RIGHT_MOTOR_PWM  19
#define RIGHT_MOTOR_INA  27
#define RIGHT_MOTOR_INB  23

// === I2C / PCA9685 ===
#define PCA9685_ADDR 0x40
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22

#define SERVOMIN  150
#define SERVOMAX  600
#define SERVO_MAX_ANGLE 270.0

// === КАНАЛЫ СЕРВ ===
#define TEST_SERVO_NUM  0     // Поворот основания
#define LINK1_SERVO_NUM 1     // Колонна 1
#define LINK2_SERVO_NUM 2     // Колонна 2
#define ROTATE_GRIP_NUM 3     // Вращение хвата
#define GRIPPER_SERVO_NUM 4   // Сжатие/разжатие

// ============================================
// === НАСТРОЙКИ МАНИПУЛЯТОРА (КРУТИ ЗДЕСЬ!) ===
// ============================================

// Скорость поворота основания (больше = медленнее)
#define BASE_SPEED_DIV 150.0

// Скорость колонн (больше = медленнее)
#define ARM_SPEED_DIV 150.0

// Скорость вращения хвата (больше = медленнее)
#define ROTATE_SPEED_DIV 150.0

// Скорость хвата (LT/RT). Больше = медленнее
#define GRIPPER_SPEED 5.0

// === ЛИМИТЫ КОЛОНН ===
#define LINK1_OFFSET    0.0
#define LINK1_MIN_ANGLE 0.0
#define LINK1_MAX_ANGLE 240.0
#define LINK1_INVERTED  true

#define LINK2_OFFSET    0.0
#define LINK2_MIN_ANGLE 0.0
#define LINK2_MAX_ANGLE 240.0
#define LINK2_INVERTED  false

// === ЛИМИТЫ ХВАТА ===
#define GRIPPER_MIN 0.0
#define GRIPPER_MAX 100.0

// === ПОДВЕСКА ===
#define SUSPENSION_R_NUM 14
#define SUSPENSION_L_NUM 15

#endif