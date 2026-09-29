# camera_manager.py
import cv2
import threading
import queue
import time
import platform


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
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            if self.running:
                print(f"[{self.name}] Уже запущена")
                return
            self.running = True
            self.thread = threading.Thread(target=self._update, daemon=True)
            self.thread.start()

    def _choose_backend(self):
        sys_name = platform.system()
        if sys_name == "Windows":
            return cv2.CAP_DSHOW
        if sys_name == "Linux":
            return cv2.CAP_V4L2
        return cv2.CAP_ANY

    def _open_capture(self):
        backend = self._choose_backend()
        cap = cv2.VideoCapture(self.source, backend)
        if not cap.isOpened() and backend != cv2.CAP_ANY:
            # Фолбэк, если конкретный backend не сработал
            cap.release()
            cap = cv2.VideoCapture(self.source, cv2.CAP_ANY)
        return cap

    def _update(self):
        self.cap = self._open_capture()
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.cap.isOpened():
            print(f"[{self.name}] Камера {self.source} не открылась")
            self.ok = False
            with self._lock:
                self.running = False
            return

        self.ok = True
        print(f"[{self.name}] Камера {self.source} открыта")

        for _ in range(10):
            self.cap.read()

        while True:
            with self._lock:
                if not self.running:
                    break

            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass

            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                # На случай гонки между get/put
                pass

        self.cap.release()
        self.ok = False

    def get_frame(self):
        try:
            return self.frame_queue.get_nowait()
        except queue.Empty:
            return None

    def stop(self):
        with self._lock:
            self.running = False

        if self.thread:
            self.thread.join(timeout=2.0)
            if self.thread.is_alive():
                print(f"[{self.name}] Поток камеры не завершился за timeout")


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