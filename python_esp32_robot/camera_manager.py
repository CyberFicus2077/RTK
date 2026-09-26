# camera_manager.py
"""
Менеджер двух USB-камер (SkyDroid).
- Каждая камера читается в своём потоке.
- Основной цикл не блокируется.
- Режимы: cam1 / cam2 (переключаются по кнопке B).
"""

import cv2
import threading
import queue
import time


class CameraStream:
    def __init__(self, source, name, width=640, height=480):
        self.source = source
        self.name = name
        self.width = width
        self.height = height
        self.frame_queue = queue.Queue(maxsize=1)
        self.running = False
        self.thread = None
        self.cap = None
        self.ok = False

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        self.cap = cv2.VideoCapture(self.source, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.cap.isOpened():
            print(f"[{self.name}] Камера {self.source} не открылась")
            self.ok = False
            return

        self.ok = True
        print(f"[{self.name}] Камера {self.source} открыта")

        for _ in range(10):
            self.cap.read()

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
            self.frame_queue.put(frame)

        self.cap.release()

    def get_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)


class CameraManager:
    MODE_CAM1 = "cam1"
    MODE_CAM2 = "cam2"

    def __init__(self, source1, source2):
        self.cam1 = CameraStream(source1, "cam1")
        self.cam2 = CameraStream(source2, "cam2")
        self.mode = self.MODE_CAM1

    def start(self):
        self.cam1.start()
        self.cam2.start()

    def stop(self):
        self.cam1.stop()
        self.cam2.stop()

    def toggle_mode(self):
        self.mode = self.MODE_CAM2 if self.mode == self.MODE_CAM1 else self.MODE_CAM1
        print(f"[CameraManager] Режим: {self.mode}")
        return self.mode

    def get_active_frame(self):
        if self.mode == self.MODE_CAM1:
            return self.cam1.get_frame()
        return self.cam2.get_frame()