# config.py
import math

# Сетевые настройки (робот)
ESP32_IP = "192.168.10.101"
PORT = 99
START_BYTE = 0xAA

# --- Камеры (два SkyDroid через USB) ---
# Индексы из test_cam.py. Пример:
#   CAM1_URL = 1   # первый SkyDroid
#   CAM2_URL = 2   # второй SkyDroid
CAM1_URL = 1
CAM2_URL = 2

JOY_X_AXIS = 0
JOY_Y_AXIS = 1
JOY_RIGHT_X_AXIS = 2
JOY_RIGHT_Y_AXIS = 3

TURN_SENSITIVITY = 1.5

SPIN_ANGLE_RAD = math.pi / 7
SPIN_Y_LIMIT = 0.2

SILENCE_ANGLE_RAD = math.pi / 7
SILENCE_Y_LIMIT = 0.21

BTN_BACK = 6
BTN_START = 7
BTN_SWITCH_CAM = 1   # кнопка B на Xbox