import cv2
import numpy as np


class RobotVision:
    DEFAULT_THRESHOLD = 60
    THRESHOLD_MAX = 255

    def __init__(self, camera_index=None):
        self.cap = None
        if camera_index is not None:
            self.cap = cv2.VideoCapture(camera_index)
            if not self.cap.isOpened():
                print(f"Предупреждение: камера {camera_index} недоступна. Пробуем индекс 0...")
                self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise RuntimeError("Не удалось подключиться ни к одной камере.")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            for _ in range(10):
                self.cap.read()

        self.qr_detector = cv2.QRCodeDetector()
        self.last_qr = None
        self.last_cx = None

        self.use_otsu = False
        self.thresh_value = self.DEFAULT_THRESHOLD

        self.last_error = 0.0
        self.lost_frames = 0
        self._qr_error_count = 0

        self.debug_window = "Binary Threshold (Debug)"
        cv2.namedWindow(self.debug_window, cv2.WINDOW_NORMAL)
        cv2.createTrackbar(
            "Darkness",
            self.debug_window,
            self.thresh_value,
            self.THRESHOLD_MAX,
            self._on_threshold_change,
        )
        cv2.resizeWindow(self.debug_window, 480, 300)

    def _on_threshold_change(self, value):
        self.thresh_value = int(value)

    def set_otsu(self, enabled: bool):
        self.use_otsu = bool(enabled)

    def reset_threshold(self):
        self.thresh_value = self.DEFAULT_THRESHOLD

    def _detect_qr(self, frame):
        try:
            data, bbox, _ = self.qr_detector.detectAndDecode(frame)
            return data, bbox
        except cv2.error as e:
            self._qr_error_count += 1
            if self._qr_error_count <= 3:
                print(f"[QR] OpenCV error #{self._qr_error_count}: {e}")
            return None, None

    @staticmethod
    def _build_histogram(gray, thresh_value):
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        peak = hist.max() if hist.max() > 0 else 1.0
        hh, ww = 100, 256
        img = np.full((hh, ww, 3), 255, np.uint8)

        for i in range(256):
            y = int(hh - (hist[i] / peak) * (hh - 12))
            cv2.line(img, (i, hh - 1), (i, y), (170, 170, 170), 1)

        x = int(np.clip(thresh_value, 0, 255))
        cv2.line(img, (x, 0), (x, hh - 1), (0, 0, 255), 2)
        cv2.putText(img, f"thr={thresh_value}", (5, 14),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 0, 0), 1)
        cv2.putText(img, "dark (line)", (5, hh - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 0), 1)
        cv2.putText(img, "bright (floor)", (ww - 105, hh - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 0), 1)
        return img

    def process_frame(self, frame, auto_mode=True, debug=True,
                      coast_after_lost=True, max_lost_frames=20):
        if frame is None:
            if self.cap is None:
                return None, None, self.last_qr
            ret, frame = self.cap.read()
            if not ret or frame is None or frame.size == 0:
                return None, None, self.last_qr

        if frame is None or frame.size == 0:
            return frame, None, self.last_qr

        h, w = frame.shape[:2]

        data, bbox = self._detect_qr(frame)
        if data:
            self.last_qr = data
            if bbox is not None:
                pts = bbox.astype(int)
                cv2.polylines(frame, [pts], True, (0, 255, 255), 2)
                cv2.putText(frame, f"QR: {data}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        error = None
        if auto_mode:
            roi_top = int(h * 0.8)
            margin_x = int(w * 0.15)
            roi_x_start = margin_x
            roi_x_end = w - margin_x
            roi = frame[roi_top:, roi_x_start:roi_x_end]

            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)

            if self.use_otsu:
                _, thresh = cv2.threshold(
                    blur, 0, 255,
                    cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            else:
                _, thresh = cv2.threshold(
                    blur, self.thresh_value, 255,
                    cv2.THRESH_BINARY_INV)

            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

            if debug:
                mask_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
                mode = "OTSU" if self.use_otsu else f"MANUAL thr={self.thresh_value}"
                cv2.putText(mask_bgr, mode, (8, 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 255), 2)

                hist_vis = self._build_histogram(blur, self.thresh_value)
                hist_vis = cv2.resize(
                    hist_vis, (mask_bgr.shape[1], 100),
                    interpolation=cv2.INTER_NEAREST)

                cv2.imshow(self.debug_window, np.vstack([mask_bgr, hist_vis]))

            contours, _ = cv2.findContours(
                thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            valid_candidates = []
            for c in contours:
                area = cv2.contourArea(c)
                if area > 400:
                    M = cv2.moments(c)
                    if M["m00"] > 0:
                        cx_full = int(M["m10"] / M["m00"]) + roi_x_start
                        valid_candidates.append((c, cx_full, area))

            if valid_candidates:
                target_x = self.last_cx if self.last_cx is not None else (w // 2)
                best = min(
                    valid_candidates,
                    key=lambda item: abs(item[1] - target_x) / (item[2] ** 0.5),
                )
                cx = best[1]
                self.last_cx = cx
                error = (cx - (w / 2)) / (w / 2)

                self.last_error = error
                self.lost_frames = 0

                cv2.line(frame, (cx, roi_top), (cx, h), (0, 255, 0), 4)
            else:
                self.last_cx = None
                self.lost_frames += 1

                if not coast_after_lost:
                    error = None
                elif max_lost_frames > 0 and self.lost_frames > max_lost_frames:
                    error = None
                else:
                    error = self.last_error

            cv2.line(frame, (w // 2, roi_top), (w // 2, h), (255, 0, 0), 2)
            cv2.rectangle(frame, (roi_x_start, roi_top),
                          (roi_x_end, h), (100, 100, 100), 1)

        return frame, error, self.last_qr

    def release(self):
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()