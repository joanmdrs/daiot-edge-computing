import cv2
import face_recognition
import numpy as np
import time
import paho.mqtt.client as mqtt
import json  # Importa a biblioteca para trabalhar com JSON

# --- Configurações MQTT ---
MQTT_BROKER_IP = "192.168.1.10"  # Ex: "192.168.1.10"
MQTT_PORT = 1883
MQTT_USER = "usermqtt"
MQTT_PASS = "passmqtt"
MQTT_TOPIC_STATE = "face_recognition/status" # Tópico para o estado do sensor

# --- Configurações de Descoberta MQTT ---
# O tópico de descoberta segue a convenção: homeassistant/<componente>/<node_id>/<object_id>/config
MQTT_TOPIC_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/status/config"

# Payload JSON para configurar o sensor
DISCOVERY_PAYLOAD = {
    "name": "Último Rosto Reconhecido",
    "state_topic": MQTT_TOPIC_STATE,
    "unique_id": "face_recognition_cam_status",
    "icon": "mdi:face-recognition",
    # Adiciona informações sobre o dispositivo para agrupar entidades
    "device": {
        "identifiers": ["facial_recognition_cam_01"],
        "name": "Câmera de Reconhecimento Facial",
        "model": "Raspberry Pi/PC Webcam",
        "manufacturer": "DIY"
    }
}

# Função para conectar ao broker MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Conectado ao broker MQTT!")
        # Publica o payload de descoberta após a conexão
        publish_discovery_payload(client)
    else:
        print(f"❌ Falha na conexão. Código de retorno: {rc}")

def publish_discovery_payload(client):
    """Publica a mensagem de descoberta para o Home Assistant."""
    # O payload precisa ser uma string JSON
    payload_str = json.dumps(DISCOVERY_PAYLOAD)
    # O retain=True faz com que a mensagem seja mantida no broker
    # e o Home Assistant a descubra mesmo se o script reiniciar.
    client.publish(MQTT_TOPIC_DISCOVERY, payload_str, retain=True)
    print("🚀 Publicando payload de descoberta para o Home Assistant...")

client = mqtt.Client()
client.on_connect = on_connect
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)
client.loop_start()

# Carregar imagem da pessoa conhecida (código existente...)
image_known = face_recognition.load_image_file("known_person.jpeg")
encodings = face_recognition.face_encodings(image_known)
if len(encodings) == 0:
    print("❌ Nenhum rosto detectado na imagem conhecida. Verifique a imagem.")
    client.disconnect()
    exit()
encoding_known = encodings[0]

# ... (restante do seu código)
video_capture = cv2.VideoCapture(0)
known_face_encodings = [encoding_known]
known_face_names = ["Pessoa Conhecida"]
last_recognized_name = None

while True:
    start_time = time.time()
    ret, frame = video_capture.read()
    if not ret:
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    
    current_recognized_name = "Desconhecido"

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Desconhecido"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            current_recognized_name = name

        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (255, 255, 255), 2)

    if current_recognized_name != last_recognized_name:
        # Publica o estado no tópico de estado (o que foi definido no payload de descoberta)
        client.publish(MQTT_TOPIC_STATE, current_recognized_name)
        print(f"📦 MQTT: Publicando '{current_recognized_name}' no tópico '{MQTT_TOPIC_STATE}'")
        last_recognized_name = current_recognized_name

    fps = 1.0 / (time.time() - start_time)
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()
client.loop_stop()
client.disconnect()