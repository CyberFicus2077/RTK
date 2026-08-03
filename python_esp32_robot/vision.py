import cv2
import numpy as np

class RobotVision:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.qr_detector = cv2.QRCodeDetector()
        self.last_qr = None

    def process_frame(self, frame, auto_mode):
        h, w = frame.shape[:2]
        
        # --- 1. Поиск QR-кода (Всегда в фоне) ---
        data, bbox, _ = self.qr_detector.detectAndDecode(frame)
        if data:
            self.last_qr = data
            if bbox is not None:
                pts = bbox.astype(int)
                cv2.polylines(frame, [pts], True, (0, 255, 255), 2)

        # --- 2. Поиск линии (Только если включен AUTO) ---
        error = None
        if auto_mode:
            roi_top = int(h * 0.5)
            roi = frame[roi_top:, :]
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)
            _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Синяя линия - центр кадра (цель)
            cv2.line(frame, (w//2, roi_top), (w//2, h), (255, 0, 0), 2)

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                if cv2.contourArea(largest_contour) > 500:
                    M = cv2.moments(largest_contour)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        error = (cx - (w / 2)) / (w / 2)
                        
                        # Рисуем контур и зеленую линию центра
                        temp_contour = largest_contour.copy()
                        temp_contour[:, :, 1] += roi_top
                        cv2.drawContours(frame, [temp_contour], -1, (0, 255, 255), 2)
                        cv2.line(frame, (cx, roi_top), (cx, h), (0, 255, 0), 4)
        
        return frame, error, self.last_qr

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()