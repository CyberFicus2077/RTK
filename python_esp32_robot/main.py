# main.py
import sys
import time
import pygame
import config
from drive import process_stick
from network import RobotNetwork


def main():
    # Инициализация pygame
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("Ошибка: Геймпад не обнаружен! Подключи его и перезапусти.")
        sys.exit()

    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Робот готов к управлению через: {joystick.get_name()}")

    # Запуск сети
    net = RobotNetwork()
    print(f"Отправка UDP пакетов на {config.ESP32_IP}:{config.PORT}")

    # Индексы кнопок для стандартного Xboxика
    A_BUTTON_INDEX = 0
    B_BUTTON_INDEX = 1
    X_BUTTON_INDEX = 2
    Y_BUTTON_INDEX = 3
    LB_BUTTON_INDEX = 4
    RB_BUTTON_INDEX = 5

    # Индексы осей для триггеров LT и RT
    # триггеры идут как оси: в покое -1.0, при полном нажатии +1.0)
    LT_AXIS_INDEX = 4  
    RT_AXIS_INDEX = 5  

    try:
        while True:
            pygame.event.pump()

            # Читаем абсолютно СЫРЫЕ оси напрямую для ходовых моторов
            raw_x = joystick.get_axis(config.JOY_X_AXIS)
            raw_y = joystick.get_axis(config.JOY_Y_AXIS)

            # Прогоняем сырые координаты через исправленное ядро движения
            left_byte, right_byte = process_stick(raw_x, raw_y)

            # 2. Читаем правый стик для манипулятора
            raw_right_x = -(joystick.get_axis(config.JOY_RIGHT_X_AXIS)) * abs(joystick.get_axis(config.JOY_RIGHT_X_AXIS)) # Инвертировал x
            raw_right_y = joystick.get_axis(config.JOY_RIGHT_Y_AXIS)

            right_x_byte = int(raw_right_x * 127 + 128)
            right_y_byte = int(raw_right_y * 127 + 128)

            # 3. Читаем дискретные состояния кнопок и триггеров
            lb_pressed = joystick.get_button(LB_BUTTON_INDEX)
            rb_pressed = joystick.get_button(RB_BUTTON_INDEX)
            
            # Считываем триггеры как оси: если прожаты глубже порога, считаем их активными (True)
            lt_pressed = joystick.get_axis(LT_AXIS_INDEX) > 0.1
            rt_pressed = joystick.get_axis(RT_AXIS_INDEX) > 0.1

            a_pressed = joystick.get_button(A_BUTTON_INDEX)
            b_pressed = joystick.get_button(B_BUTTON_INDEX)
            x_pressed = joystick.get_button(X_BUTTON_INDEX)
            y_pressed = joystick.get_button(Y_BUTTON_INDEX)

            # 4. СОБИРАЕМ НОВУЮ ВРЕМЕННУЮ БИТОВУЮ МАСКУ (Байт 5 
            # 1-й бит: LB, 2-й: RB, 3-й: LT, 4-й: RT, 5-й: A, 6-й: B, 7-й: X, 8-й: Y
            buttons1_byte = 0
            if lb_pressed: buttons1_byte |= (1 << 0)
            if rb_pressed: buttons1_byte |= (1 << 1)
            if lt_pressed: buttons1_byte |= (1 << 2)
            if rt_pressed: buttons1_byte |= (1 << 3)
            if a_pressed:  buttons1_byte |= (1 << 4)
            if b_pressed:  buttons1_byte |= (1 << 5)
            if x_pressed:  buttons1_byte |= (1 << 6)
            if y_pressed:  buttons1_byte |= (1 << 7)

            # 5. Чтение D-pad (Стрелок) для Байт 6 / buttons2
            buttons2_byte = 0
            hat = joystick.get_hat(0)  # Возвращает (x, y)
            if hat[1] == 1:  buttons2_byte |= (1 << 0)  # Вверх
            if hat[0] == 1:  buttons2_byte |= (1 << 1)  # Вправо
            if hat[0] == -1: buttons2_byte |= (1 << 2)  # Влево
            if hat[1] == -1: buttons2_byte |= (1 << 3)  # Вниз

            # Отправляем пакет на робота
            net.send_packet(
                left_motor=left_byte, 
                right_motor=right_byte, 
                joy_x=right_x_byte, 
                joy_y=right_y_byte,
                buttons1=buttons1_byte,
                buttons2=buttons2_byte
            )

            # Отладкочка в терминал ноутбука
            debug_y = -raw_y
            print(
                f"Стик Л: X={raw_x:+.2f} Y={debug_y:+.2f} | "
                f"Стик П: X={raw_right_x:+.2f} Y={raw_right_y:+.2f} | "
                f"Матч: LB={'1' if lb_pressed else '0'} LT={'1' if lt_pressed else '0'} RT={'1' if rt_pressed else '0'} B={'1' if b_pressed else '0'} | "
                f"Байт5={bin(buttons1_byte)[2:].zfill(8)}", 
                end="\r"
            )

            time.sleep(0.02)  # Частота отправки ~50 Гц

    except KeyboardInterrupt:
        print("\nПрограмма остановлена оператором.")
    finally:
        # При выходе плавно глушим робота
        net.send_packet(128, 128, 128, 128, 0, 0)
        pygame.quit()


if __name__ == "__main__":
    main()