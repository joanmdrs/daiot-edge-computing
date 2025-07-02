# main.py

import cv2
import time
import json
import datetime
from camera import Camera
from mqtt_manager import MQTTManager
from face_recognition_module import FaceRecognitionModule
from logger import Logger
from config import *

def main():
    cam = Camera()
    mqtt = MQTTManager()
    face_module = FaceRecognitionModule()
    logger = Logger()

    last_name = None
    confirmed_name = None
    consecutive = 0
    last_seen = time.time()

    try:
        while True:
            frame = cam.get_frame()
            if frame is None:
                continue

            name, location = face_module.recognize(frame)

            if not name:
                continue

            # Debounce logic
            if name == confirmed_name:
                consecutive = 0
            elif name == last_name:
                consecutive += 1
                if consecutive >= CONFIRMATION_THRESHOLD:
                    logger.log(name)
                    mqtt.publish(MQTT_TOPIC_STATE, name)

                    if name != "Desconhecido":
                        payload = json.dumps({"command": "open", "user": name})
                        mqtt.publish(MQTT_TOPIC_DOOR_CONTROL, payload)
                    else:
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        alert_payload = json.dumps({
                            "message": "Rosto desconhecido detectado!",
                            "timestamp": timestamp
                        })
                        mqtt.publish(MQTT_TOPIC_ALERT, alert_payload)

                    confirmed_name = name
                    consecutive = 0
            else:
                last_name = name
                consecutive = 1

            # Inatividade
            if name != "Nenhum Rosto Detectado":
                last_seen = time.time()
            elif time.time() - last_seen > INACTIVITY_TIMEOUT_SECONDS and confirmed_name != "Nenhum Rosto Detectado":
                mqtt.publish(MQTT_TOPIC_STATE, "Nenhum Rosto Detectado")
                confirmed_name = "Nenhum Rosto Detectado"

            # Exibe a imagem
            cv2.imshow("Reconhecimento Facial", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        mqtt.disconnect()
        cam.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
