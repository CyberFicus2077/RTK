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
        print("ОШИБКА: Геймпад не обнаружен! Подключите его и перезапустите.")
        sys.exit()

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Контроллер: {joystick.get_name()} готов.")

    net = RobotNetwork()
    vision = RobotVision()

    auto_mode = False
    last_start_state = 0
    last_back_state = 0

    # Настройка окна (сделаем его побольше)
    cv2.namedWindow("Robot Stream", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Robot Stream", 1000, 750)

    try:
        while True:
            pygame.event.pump()

            # --- 1. ЛОГИКА КНОПОК РЕЖИМА ---
            btn_start = joystick.get_button(config.BTN_START) # Три полоски
            btn_back = joystick.get_button(config.BTN_BACK)   # Два окошка

            # Переключатель Автопилота
            if btn_start and not last_start_state:
                auto_mode = not auto_mode
                print(f"\n[РЕЖИМ] Автопилот: {'АКТИВИРОВАН' if auto_mode else 'ВЫКЛЮЧЕН'}")
            last_start_state = btn_start

            # Сброс найденного QR
            if btn_back and not last_back_state:
                vision.last_qr = None
                print("\n[СИСТЕМА] Память QR очищена")
            last_back_state = btn_back

            # --- 2. ОБРАБОТКА ВИДЕО ---
            ret, frame = vision.cap.read()
            if not ret: continue

            # Обработка (полоски рисуются только если auto_mode=True)
            frame, line_error, qr_data = vision.process_frame(frame, auto_mode)

            # Вывод текста на экран
            mode_text = "AUTO PILOT" if auto_mode else "MANUAL DRIVE"
            mode_color = (0, 255, 0) if auto_mode else (0, 0, 255)
            cv2.putText(frame, mode_text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, mode_color, 2)
            
            if qr_data:
                cv2.putText(frame, f"QR: {qr_data}", (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow("Robot Stream", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'): break

            # --- 3. УПРАВЛЕНИЕ МОТОРАМИ ---
            if auto_mode:
                if line_error is not None:
                    speed, kp = 30, 50 # Можно подправить под твоего робота
                    l = 128 + speed + (line_error * kp)
                    r = 128 + speed - (line_error * kp)
                    left_byte, right_byte = int(l), int(r)
                else:
                    left_byte, right_byte = 128, 128 # Стоп если линии нет
            else:
                # Читаем левый стик
                lx = joystick.get_axis(config.JOY_X_AXIS)
                ly = joystick.get_axis(config.JOY_Y_AXIS)
                left_byte, right_byte = process_stick(lx, ly)

            # --- 4. МАНИПУЛЯТОР (Твоя логика) ---
            rx = -(joystick.get_axis(config.JOY_RIGHT_X_AXIS)) * abs(joystick.get_axis(config.JOY_RIGHT_X_AXIS))
            ry = joystick.get_axis(config.JOY_RIGHT_Y_AXIS)
            right_x_byte = int(rx * 127 + 128)
            right_y_byte = int(ry * 127 + 128)

            # Битовая маска кнопок (LB, RB, LT, RT, A, B, X, Y)
            b1 = 0
            if joystick.get_button(4): b1 |= (1 << 0) # LB
            if joystick.get_button(5): b1 |= (1 << 1) # RB
            if joystick.get_axis(4) > 0.1: b1 |= (1 << 2) # LT
            if joystick.get_axis(5) > 0.1: b1 |= (1 << 3) # RT
            if joystick.get_button(0): b1 |= (1 << 4) # A
            if joystick.get_button(1): b1 |= (1 << 5) # B
            if joystick.get_button(2): b1 |= (1 << 6) # X
            if joystick.get_button(3): b1 |= (1 << 7) # Y

            # --- 5. ОТПРАВКА ---
            net.send_packet(
                left_motor=int(max(0, min(255, left_byte))),
                right_motor=int(max(0, min(255, right_byte))),
                joy_x=right_x_byte,
                joy_y=right_y_byte,
                buttons1=b1,
                buttons2=0
            )

            time.sleep(0.01)

    except KeyboardInterrupt:
        pass
    finally:
        vision.release()
        net.send_packet(128, 128, 128, 128, 0, 0)
        pygame.quit()

if __name__ == "__main__":
    main()