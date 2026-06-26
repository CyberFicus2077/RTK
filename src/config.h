
#ifndef CONFIG_H
#define CONFIG_H

const char* ssid = "K-LAB";
const char* password = "allhailklab";
#define UDP_PORT 99

#define START_BYTE 0xAA  // Синхробайт, идёт первым в пакете (0xAA = 170 в dec)
#define PACKET_SIZE 8    // Полный размер пакета с синхробайтом и CRC
#define FAILSAFE_TIMEOUT 500 // Время в мс, после которого робот отрубается

// Левый мотор
#define LEFT_MOTOR_PWM  26
#define LEFT_MOTOR_INA  33
#define LEFT_MOTOR_INB  25

// Правый мотор
#define RIGHT_MOTOR_PWM  19
#define RIGHT_MOTOR_INA  27
#define RIGHT_MOTOR_INB  23

// Пины для сервоприводов (Ручка)
#define PCA9685_ADDR 0x40
#define I2C_SDA_PIN 21
#define I2C_SCL_PIN 22


#define SERVOMIN  150 
#define SERVOMAX  600 
#define SERVO_MAX_ANGLE 270.0 

// ТЕСТОВАЯ СЕРВА (Поворот основания, Байт 3 - X)
#define TEST_SERVO_NUM 0       

// СЕРВА 2: ПЕРВАЯ КОЛОННА (Байт 4 - Y без LB)
#define LINK1_SERVO_NUM 1
#define LINK1_OFFSET    0.0     
#define LINK1_MIN_ANGLE 0.0     // Разрешаем опускаться до самого низа
#define LINK1_MAX_ANGLE 215.0   //рабочий диапазон первой сервы
#define LINK1_INVERTED  true

// СЕРВА 3: ВТОРАЯ КОЛОННА (Байт 4 - Y с зажатой LB)
#define LINK2_SERVO_NUM 2
#define LINK2_OFFSET    0.0     
#define LINK2_MIN_ANGLE 0.0     // Снижаем лимит, чтобы серва не блокировалась на 15 градусах
#define LINK2_MAX_ANGLE 240.0
#define LINK2_INVERTED  false    // ВКЛЮЧАЕМ ИНВЕРСИЮ ДЛЯ ВТОРОЙ СЕРВЫ

// СЕРВОПРИВОДЫ ПОДВЕСКИ (помянем)
#define SUSPENSION_R_NUM 14
#define SUSPENSION_L_NUM 15

//#define PIN_SERVO_BASE   25  // Основание
//#define PIN_SERVO_ELBOW  26  // Локоть
//#define PIN_SERVO_WRIST  32  // Кисть
//#define PIN_SERVO_CLAW   33  // Схват

//#define PIN_SUSP_LEFT    19  // Левая качель
//#define PIN_SUSP_RIGHT   18  // Правая качель

#endif