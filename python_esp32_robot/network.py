# network.py
import socket
import config


class RobotNetwork:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send_packet(
        self,
        left_motor,
        right_motor,
        joy_x=128,
        joy_y=128,
        buttons1=0,
        buttons2=0,
    ):
        """Формирует пакет из 8 байт (Синхробайт + 6 данных + CRC) и отправляет на ESP32."""
        packet = bytearray([
            config.START_BYTE,
            int(left_motor) & 0xFF,
            int(right_motor) & 0xFF,
            int(joy_x) & 0xFF,
            int(joy_y) & 0xFF,
            int(buttons1) & 0xFF,
            int(buttons2) & 0xFF,
        ])

        # Считаем контрольную сумму (сложение байт с 1 по 6)
        crc = 0
        for i in range(1, 7):
            crc = (crc + packet[i]) & 0xFF

        packet.append(crc)

        # Отправляем на робота
        try:
            self.sock.sendto(packet, (config.ESP32_IP, config.PORT))
        except Exception as e:
            print(f"\nОшибка сети: {e}")