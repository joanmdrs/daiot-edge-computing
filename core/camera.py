# camera.py

import cv2
from config import CAMERA_INDEX

class Camera:
    def __init__(self):
        print("🎥 Inicializando a câmera...")
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)
        if not self.video_capture.isOpened():
            raise Exception("❌ Erro: Não foi possível abrir a câmera.")

    def get_frame(self):
        ret, frame = self.video_capture.read()
        if not ret:
            print("⚠️ Não foi possível capturar o frame.")
            return None
        return frame

    def release(self):
        self.video_capture.release()
        print("✅ Câmera liberada.")
