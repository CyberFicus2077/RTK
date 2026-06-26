# drive.py
import math
import config

def process_stick(x, y):
    # Зона нечувствительности в самом центре стика (deadzone)
    if abs(x) < 0.05 and abs(y) < 0.05:
        return 128, 128

    radius = math.hypot(x, y)
    if radius > 1.0: radius = 1.0

    # Считаем честный угол от горизонтали (от -pi до pi)
    angle = math.atan2(y, x)
    abs_angle = abs(angle)

    # Наш ход: вверх (+1.0), вниз (-1.0)
    drive = -y 

    # Определяем, в каком конусе находимся
    is_in_right_cone = abs_angle <= config.SPIN_ANGLE_RAD
    is_in_left_cone = abs_angle >= (math.pi - config.SPIN_ANGLE_RAD)
    is_in_spin_y = abs(drive) < config.SPIN_Y_LIMIT

    if (is_in_right_cone or is_in_left_cone) and is_in_spin_y:
        # Базовая скорость от радиуса
        base_speed = radius * 127

        # Находим отклонение угла от идеальной горизонтали (в радианах)
        if is_in_right_cone:
            angle_deviation = abs_angle  # Для правого конуса идеальный ноль - это 0
        else:
            angle_deviation = math.pi - abs_angle # Для левого идеальный ноль - это pi

        spin_speed = base_speed

        if y > 0:
            # Расчет коэффициентов затухания (от 1.0 в идеале до 0.0 на границе зоны)
            # 1. Затухание по углу (чем ближе к краю конуса, тем меньше коэффициент)
            angle_fade = 1.0 - (angle_deviation / config.SPIN_ANGLE_RAD)
            
            # 2. Затухание по высоте Y (чем ближе к SPIN_Y_LIMIT, тем меньше коэффициент)
            y_fade = 1.0 - (abs(drive) / config.SPIN_Y_LIMIT)

            # Объединяем затухание (мультипликативно для идеальной плавности во все стороны)
            fade_factor = angle_fade * y_fade

            # Вычисляем финальную скорость разворота с учетом демпфирования
            spin_speed = int(base_speed * fade_factor)
        
        if x >= 0:
            # Разворот вправо
            return 128 + spin_speed, 128 - spin_speed
        else:
            # Разворот влево
            return 128 - spin_speed, 128 + spin_speed

    if y > 0:
        is_in_silence_angle = (abs_angle <= config.SILENCE_ANGLE_RAD) or (abs_angle >= (math.pi - config.SILENCE_ANGLE_RAD))
        is_in_silence_y = abs(drive) < config.SILENCE_Y_LIMIT

        if is_in_silence_angle and is_in_silence_y:
            return 128, 128  # Блокировка моторов (тишина)

    # Экспоненциальный руль
    steer = math.copysign(abs(x) ** config.TURN_SENSITIVITY, x)

    # Автомобильный реверс руля при движении назад
    if drive < 0:
        steer = -steer

    # Танковое микширование
    left = drive + steer
    right = drive - steer

    # Нормализация
    max_val = max(abs(left), abs(right))
    if max_val > 1.0:
        left /= max_val
        right /= max_val

    # В байты
    left_motor = int(left * 127 + 128)
    right_motor = int(right * 127 + 128)

    return left_motor, right_motor