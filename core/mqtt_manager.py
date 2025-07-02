# mqtt_manager.py

import json
import paho.mqtt.client as mqtt
from config import *

class MQTTManager:
    def __init__(self):
        print("🔌 Conectando ao broker MQTT...")
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.on_connect = self.on_connect
        self.client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("✅ Conectado ao broker MQTT.")
            self.publish_discovery()
        else:
            print(f"❌ Falha na conexão MQTT. Código: {rc}")

    def publish_discovery(self):
        self.publish(MQTT_TOPIC_DISCOVERY, json.dumps({
            "name": "Último Rosto Reconhecido",
            "state_topic": MQTT_TOPIC_STATE,
            "unique_id": "face_recognition_cam_status",
            "icon": "mdi:face-recognition",
            "device": {
                "identifiers": ["facial_recognition_cam_01"],
                "name": "Câmera de Reconhecimento Facial",
                "model": "PC Webcam",
                "manufacturer": "DIY"
            }
        }), retain=True)

        self.publish(MQTT_TOPIC_DOOR_DISCOVERY, json.dumps({
            "name": "Comando Porta Reconhecimento Facial",
            "state_topic": MQTT_TOPIC_DOOR_CONTROL,
            "unique_id": "face_recognition_cam_door_command",
            "value_template": "{% if value_json.command == 'open' %}mdi:check-circle-outline{% else %}mdi:lock{% endif %}",
            "icon_template": "{{ states('sensor.comando_porta_reconhecimento_facial') }}",
            "json_attributes_topic": MQTT_TOPIC_DOOR_CONTROL,
            "device": {
                "identifiers": ["facial_recognition_cam_01"]
            }
        }), retain=True)

        self.publish(MQTT_TOPIC_ALERT_DISCOVERY, json.dumps({
            "name": "Alerta Rosto Desconhecido",
            "state_topic": MQTT_TOPIC_ALERT,
            "unique_id": "face_recognition_cam_unknown_alert",
            "value_template": "{{ value_json.message }}",
            "json_attributes_topic": MQTT_TOPIC_ALERT,
            "icon": "mdi:alert",
            "device": {
                "identifiers": ["facial_recognition_cam_01"]
            }
        }), retain=True)

    def publish(self, topic, payload, retain=False):
        self.client.publish(topic, payload, retain=retain)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        print("✅ Cliente MQTT desconectado.")
