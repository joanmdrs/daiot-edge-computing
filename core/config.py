# config.py

import os
import time

# MQTT Configuration
MQTT_BROKER_IP = "192.168.3.126"
MQTT_PORT = 1883
MQTT_USER = "usermqtt"
MQTT_PASS = "passmqtt"

MQTT_TOPIC_STATE = "face_recognition/status"
MQTT_TOPIC_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/status/config"
MQTT_TOPIC_DOOR_CONTROL = "face_recognition/door_control"
MQTT_TOPIC_DOOR_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/door_command/config"
MQTT_TOPIC_ALERT = "face_recognition/alert"
MQTT_TOPIC_ALERT_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/unknown_alert/config"

# Face Recognition
KNOWN_FACES_DIR = "known_faces"
UNKNOWN_FACES_DIR = "unknown_faces"
FACE_TOLERANCE = 0.6  # quanto menor, mais rigoroso
SCALE_FACTOR = 0.25  # para redimensionar o frame

# Debounce e inatividade
CONFIRMATION_THRESHOLD = 5
INACTIVITY_TIMEOUT_SECONDS = 30

# Log
LOG_FILE = "recognition_history.csv"

# Banco de dados
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///recognition.db")

# Câmera
CAMERA_INDEX = 0  # 0 = webcam local; ou use a URL de stream de celular (ex: "http://192.168.0.10:8080/video")

# Segurança
ALERT_INTERVAL_SECONDS = 10
