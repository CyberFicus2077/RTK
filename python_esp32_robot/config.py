# config.py
import math

# === СЕТЬ ===
ESP32_IP = "192.168.10.101"
PORT = 99
START_BYTE = 0xAA

# === КАМЕРЫ ===
USE_CAMERA = True  # ← True = камеры, False = без камер
CAM1_URL = 1
CAM2_URL = 2

# === ОСИ ГЕЙМПАДА ===
JOY_X_AXIS = 0
JOY_Y_AXIS = 1
JOY_RIGHT_X_AXIS = 2
JOY_RIGHT_Y_AXIS = 3
JOY_LT_AXIS = 4
JOY_RT_AXIS = 5

# === НАСТРОЙКИ ДВИЖЕНИЯ ===
TURN_SENSITIVITY = 1.5      # кривая руля
SPIN_ANGLE_RAD = math.pi / 7
SPIN_Y_LIMIT = 0.2
SILENCE_ANGLE_RAD = math.pi / 7
SILENCE_Y_LIMIT = 0.21

# ============================================
# === НАСТРОЙКИ МАНИПУЛЯТОРА (КРУТИ ЗДЕСЬ!) ===
# ============================================

# Мёртвая зона стика (0.05-0.20). Больше = менее чувствительный
MANIP_DEADZONE = 0.07

# Кривая отклика: 1.0 = линейно, 2.0 = квадратично (плавно),
# 3.0 = кубически (очень плавно в центре)
MANIP_CURVE = 2.5

# Множитель скорости в Python (0.5 = медленно, 1.0 = норм, 2.0 = быстро)
MANIP_SPEED_MULT = 2.0

# Максимальное отклонение стика (1.0 = полный ход)
MANIP_MAX_OUTPUT = 1.0

# === КНОПКИ ===
BTN_BACK = 6
BTN_START = 7
BTN_SWITCH_CAM = 3   # Y