# face_recognition_module.py

import face_recognition
import os
from config import KNOWN_FACES_DIR
import cv2


class FaceRecognitionModule:
    def __init__(self):
        self.known_encodings = []
        self.known_names = []
        self.load_faces()

    def load_faces(self):
        print(f"🔄 Carregando rostos conhecidos de '{KNOWN_FACES_DIR}'...")
        if not os.path.exists(KNOWN_FACES_DIR):
            raise Exception(f"❌ Pasta '{KNOWN_FACES_DIR}' não encontrada.")

        for file in os.listdir(KNOWN_FACES_DIR):
            if file.endswith(('.jpg', '.jpeg', '.png')):
                name = os.path.splitext(file)[0]
                path = os.path.join(KNOWN_FACES_DIR, file)
                image = face_recognition.load_image_file(path)
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name.replace('_', ' ').title())
                    print(f"✅ {name} carregado.")
                else:
                    print(f"⚠️ Nenhum rosto detectado em '{file}'.")

        if not self.known_encodings:
            raise Exception("❗ Nenhum rosto válido foi carregado.")

    def recognize(self, frame):
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_small_frame)
        encodings = face_recognition.face_encodings(rgb_small_frame, locations)

        if not encodings:
            return None, None

        face_encoding = encodings[0]
        distances = face_recognition.face_distance(self.known_encodings, face_encoding)

        if len(distances) == 0:
            return "Desconhecido", locations[0]

        best_match = min(enumerate(distances), key=lambda x: x[1])
        index, distance = best_match

        if distance < 0.6:
            return self.known_names[index], locations[0]
        return "Desconhecido", locations[0]
