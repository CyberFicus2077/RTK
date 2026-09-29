import math
import config


def process_stick(x, y):
    # Зона нечувствительности в центре стика
    if abs(x) < 0.05 and abs(y) < 0.05:
        return 128, 128

    radius = math.hypot(x, y)
    if radius > 1.0:
        radius = 1.0

    angle = math.atan2(y, x)
    abs_angle = abs(angle)

    # Вперед = +drive
    drive = -y

    is_in_right_cone = abs_angle <= config.SPIN_ANGLE_RAD
    is_in_left_cone = abs_angle >= (math.pi - config.SPIN_ANGLE_RAD)
    is_in_spin_y = abs(drive) < config.SPIN_Y_LIMIT

    if (is_in_right_cone or is_in_left_cone) and is_in_spin_y:
        base_speed = radius * 127

        if is_in_right_cone:
            angle_deviation = abs_angle
        else:
            angle_deviation = math.pi - abs_angle

        spin_speed = base_speed

        if y > 0:
            angle_fade = 1.0 - (angle_deviation / config.SPIN_ANGLE_RAD)
            y_fade = 1.0 - (abs(drive) / config.SPIN_Y_LIMIT)
            fade_factor = angle_fade * y_fade
            spin_speed = int(base_speed * fade_factor)

        if x >= 0:
            return 128 + spin_speed, 128 - spin_speed
        return 128 - spin_speed, 128 + spin_speed

    if y > 0:
        is_in_silence_angle = (
            abs_angle <= config.SILENCE_ANGLE_RAD
            or abs_angle >= (math.pi - config.SILENCE_ANGLE_RAD)
        )
        is_in_silence_y = abs(drive) < config.SILENCE_Y_LIMIT

        if is_in_silence_angle and is_in_silence_y:
            return 128, 128

    steer = math.copysign(abs(x) ** config.TURN_SENSITIVITY, x)

    if drive < 0:
        steer = -steer

    left = drive + steer
    right = drive - steer

    max_val = max(abs(left), abs(right))
    if max_val > 1.0:
        left /= max_val
        right /= max_val

    left_motor = int(left * 127 + 128)
    right_motor = int(right * 127 + 128)

    return left_motor, right_motor