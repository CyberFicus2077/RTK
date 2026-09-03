import sys
import time
import pygame
import cv2
import config
from drive import process_stick
from network import RobotNetwork
from vision import RobotVision

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
    vision = RobotVision()

    auto_mode = False
    last_start_state = 0
    last_back_state = 0

    try:
        while True:
            pygame.event.pump()

            # --- 1. Кнопки режимов ---
            btn_start = joystick.get_button(config.BTN_START)
            btn_back = joystick.get_button(config.BTN_BACK)

            if btn_start and not last_start_state:
                auto_mode = not auto_mode
                print(f"AUTO MODE: {'ON' if auto_mode else 'OFF'}")
            last_start_state = btn_start

            if btn_back and not last_back_state:
                vision.last_qr = None
                print("QR Reset")
            last_back_state = btn_back

            # --- 2. Обработка видео ---
            ret, frame = vision.cap.read()
            left_byte, right_byte = 128, 128

            if ret:
                frame, line_error, qr_data = vision.process_frame(frame, auto_mode)
                
                # UI в окне
                cv2.putText(frame, f"AUTO: {'ON' if auto_mode else 'OFF'}", (20, 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if auto_mode else (0, 0, 255), 2)
                if qr_data:
                    cv2.putText(frame, f"QR: {qr_data}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                
                cv2.imshow("Robot Controller", frame)
                cv2.waitKey(1)

            # --- 3. Движение ---
            if auto_mode:
                if line_error is not None:
                    speed, kp = 35, 50
                    left_byte = int(128 + speed + (line_error * kp))
                    right_byte = int(128 + speed - (line_error * kp))
            else:
                left_byte, right_byte = process_stick(joystick.get_axis(0), joystick.get_axis(1))

            # --- 4. Манипулятор и Клешня ---
            # Читаем правый стик (твоя математика)
            axis_rx = joystick.get_axis(2)
            raw_rx = -axis_rx * abs(axis_rx)
            raw_ry = joystick.get_axis(3)
            right_x_byte = int(raw_rx * 127 + 128)
            right_y_byte = int(raw_ry * 127 + 128)

            # Читаем триггеры (проверяем оси 2, 4 и 5 для универсальности)
            val_lt = max(joystick.get_axis(2) if abs(joystick.get_axis(2)) > 0.01 else -1, joystick.get_axis(4))
            val_rt = joystick.get_axis(5)
            
            # Нажат ли курок (учитываем, что покой может быть -1.0)
            lt_active = val_lt > 0.2 # Для Xbox это сработает
            rt_active = val_rt > 0.2

            # Сборка пакета (Байт 5)
            b1 = 0
            if joystick.get_button(4): b1 |= (1 << 0) # LB
            if joystick.get_button(5): b1 |= (1 << 1) # RB
            if lt_active:             b1 |= (1 << 2) # LT (в бит 2 для ESP32)
            if rt_active:             b1 |= (1 << 3) # RT (в бит 3 для ESP32)
            if joystick.get_button(0): b1 |= (1 << 4) # A
            if joystick.get_button(1): b1 |= (1 << 5) # B
            if joystick.get_button(2): b1 |= (1 << 6) # X
            if joystick.get_button(3): b1 |= (1 << 7) # Y

            # --- 5. Отправка пакета ---
            net.send_packet(
                left_motor=int(max(0, min(255, left_byte))),
                right_motor=int(max(0, min(255, right_byte))),
                joy_x=right_x_byte, joy_y=right_y_byte,
                buttons1=b1, buttons2=0
            )

            # Отладка в консоль (проверь LT и RT тут!)
            print(f"LT: {val_lt:+.2f} RT: {val_rt:+.2f} | B5: {bin(b1)[2:].zfill(8)} | IP:{config.ESP32_IP}", end="\r")
            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        vision.release()
        net.send_packet(128, 128, 128, 128, 0, 0)
        pygame.quit()

if __name__ == "__main__":
    main()