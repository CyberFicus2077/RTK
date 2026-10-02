import sys
import time
import math
import platform
import pygame
import cv2
import config
from drive import process_stick
from network import RobotNetwork

if getattr(config, 'USE_CAMERA', False):
    from vision import RobotVision

def clamp_u8(v):
    return int(max(0, min(255, int(v))))

def open_capture(source):
    sys_name = platform.system()
    if sys_name == "Windows":
        backend = cv2.CAP_DSHOW
    elif sys_name == "Linux":
        backend = cv2.CAP_V4L2
    else:
        backend = cv2.CAP_ANY

    cap = cv2.VideoCapture(source, backend)
    if not cap.isOpened() and backend != cv2.CAP_ANY:
        cap.release()
        cap = cv2.VideoCapture(source, cv2.CAP_ANY)

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

def process_manipulator(axis_rx, axis_ry):
    if abs(axis_rx) < getattr(config, 'MANIP_DEADZONE', 0.07):
        axis_rx = 0.0
    if abs(axis_ry) < getattr(config, 'MANIP_DEADZONE', 0.07):
        axis_ry = 0.0

    def curve(v):
        curve_val = getattr(config, 'MANIP_CURVE', 2.0)
        speed_mult = getattr(config, 'MANIP_SPEED_MULT', 1.0)
        if v >= 0:
            return (v ** curve_val) * speed_mult
        else:
            return -((-v) ** curve_val) * speed_mult

    rx = curve(axis_rx)
    ry = curve(axis_ry)

    max_out = getattr(config, 'MANIP_MAX_OUTPUT', 1.0)
    rx = max(-max_out, min(max_out, rx))
    ry = max(-max_out, min(max_out, ry))

    rx = -rx
    return rx, ry

def main():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("Ошибка: Подключи геймпад!")
        sys.exit()

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Подключен: {joystick.get_name()}")

    net = RobotNetwork()

    vision = None
    vision_ok = False
    sources = [getattr(config, 'CAM1_URL', 0), getattr(config, 'CAM2_URL', 1)]
    current_cam = 0

    if getattr(config, 'USE_CAMERA', False):
        try:
            vision = RobotVision(camera_index=sources[current_cam])
            vision.cap.release()
            vision.cap = open_capture(sources[current_cam])
            if not vision.cap.isOpened():
                raise RuntimeError(f"Камера не открылась")
            vision_ok = True
            print(f"✅ Камера подключена")
        except Exception as e:
            print(f"⚠️ Камера недоступна: {e}")
            vision_ok = False

    auto_mode = False
    last_start_state = 0
    last_back_state = 0
    last_cam_switch_state = 0

    try:
        while True:
            pygame.event.pump()

            btn_start = joystick.get_button(config.BTN_START)
            btn_back = joystick.get_button(config.BTN_BACK)
            btn_switch = joystick.get_button(getattr(config, 'BTN_SWITCH_CAM', 3))

            if btn_start and not last_start_state:
                auto_mode = not auto_mode
            last_start_state = btn_start

            if btn_back and not last_back_state:
                if vision is not None:
                    vision.last_qr = None
            last_back_state = btn_back

            if btn_switch and not last_cam_switch_state and vision_ok:
                if vision.cap is not None:
                    vision.cap.release()
                    vision.cap = None
                current_cam = (current_cam + 1) % len(sources)
                vision.cap = open_capture(sources[current_cam])
            last_cam_switch_state = btn_switch

            left_byte, right_byte = 128, 128
            line_error = None

            if vision_ok and vision.cap is not None:
                ret, frame = vision.cap.read()
                if ret and frame is not None:
                    frame, line_error, qr_data = vision.process_frame(frame, auto_mode)
                    cv2.imshow("Robot Controller", frame)
                    cv2.waitKey(1)

            if auto_mode and vision_ok and line_error is not None:
                speed, kp = 35, 50
                left_byte = clamp_u8(128 + speed + (line_error * kp))
                right_byte = clamp_u8(128 + speed - (line_error * kp))
            else:
                left_byte, right_byte = process_stick(
                    joystick.get_axis(config.JOY_X_AXIS),
                    joystick.get_axis(config.JOY_Y_AXIS),
                )

            axis_rx = joystick.get_axis(getattr(config, 'JOY_RIGHT_X_AXIS', 2))
            axis_ry = joystick.get_axis(getattr(config, 'JOY_RIGHT_Y_AXIS', 3))

            raw_rx, raw_ry = process_manipulator(axis_rx, axis_ry)

            right_x_byte = clamp_u8(raw_rx * 127 + 128)
            right_y_byte = clamp_u8(raw_ry * 127 + 128)

            val_lt = joystick.get_axis(getattr(config, 'JOY_LT_AXIS', 4))
            val_rt = joystick.get_axis(getattr(config, 'JOY_RT_AXIS', 5))

            lt_byte = clamp_u8((val_lt + 1.0) * 127.5)
            rt_byte = clamp_u8((val_rt + 1.0) * 127.5)

            lt_active = lt_byte > 40
            rt_active = rt_byte > 40

            # Байт кнопок (B5)
            b1 = 0
            if joystick.get_button(4):  b1 |= (1 << 0)
            if joystick.get_button(5):  b1 |= (1 << 1)
            if lt_active:               b1 |= (1 << 2)
            if rt_active:               b1 |= (1 << 3)
            if joystick.get_button(0):  b1 |= (1 << 4)
            if joystick.get_button(1):  b1 |= (1 << 5)
            if joystick.get_button(2):  b1 |= (1 << 6)
            if joystick.get_button(3):  b1 |= (1 << 7)

            # ЧТЕНИЕ КРЕСТОВИНЫ ДЛЯ ПОДВЕСКИ (Байт 6)
            b2 = 0
            if joystick.get_numhats() > 0:
                hat = joystick.get_hat(0)
                if hat[1] == 1:   b2 |= (1 << 0) # Вверх
                if hat[0] == 1:   b2 |= (1 << 1) # Вправо
                if hat[0] == -1:  b2 |= (1 << 2) # Влево
                if hat[1] == -1:  b2 |= (1 << 3) # Вниз

            # Отправка пакета
            net.send_packet(
                left_motor=clamp_u8(left_byte),
                right_motor=clamp_u8(right_byte),
                joy_x=right_x_byte,
                joy_y=right_y_byte,
                buttons1=b1,
                buttons2=b2, # <-- Передаем крестовину роботу
                lt_value=lt_byte,
                rt_value=rt_byte,
            )

            print(
                f"Rx:{raw_rx:+.2f} Ry:{raw_ry:+.2f} | LT:{lt_byte:3} RT:{rt_byte:3} | "
                f"B2(D-pad):{bin(b2)[2:].zfill(8)}",
                end="\r"
            )
            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        if vision is not None:
            vision.release()
        net.send_packet(128, 128, 128, 128, 0, 0)
        pygame.quit()

if __name__ == "__main__":
    main()