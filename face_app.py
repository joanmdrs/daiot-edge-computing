import cv2
import face_recognition
import numpy as np
import time
import os
import paho.mqtt.client as mqtt
import json
import csv  # Novo: Importa a biblioteca CSV
from datetime import datetime  # Novo: Importa a biblioteca de data e hora

# ====================================================================
# --- 1. CONFIGURAÇÕES DA APLICAÇÃO ---
# ====================================================================

# Configurações MQTT
MQTT_BROKER_IP = "192.168.1.10"
MQTT_PORT = 1883
MQTT_USER = "usermqtt"
MQTT_PASS = "passmqtt"
MQTT_TOPIC_STATE = "face_recognition/status"
MQTT_TOPIC_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/status/config"

# Diretório para as imagens de pessoas conhecidas
KNOWN_FACES_DIR = "known_faces"

# Novo: Configuração do arquivo de log
LOG_FILE = "recognition_history.csv"

# ====================================================================
# --- 2. CLASSE PRINCIPAL DA APLICAÇÃO ---
# ====================================================================

class FaceRecognitionApp:
    """
    Uma classe para gerenciar a aplicação de reconhecimento facial.
    Organiza a lógica de inicialização, execução e encerramento.
    """
    def __init__(self):
        """Inicializa a aplicação, carregando dados e configurando a câmera."""
        print("🚀 Inicializando a aplicação...")
        self.known_face_encodings = []
        self.known_face_names = []
        self.last_recognized_name = None
        self.load_known_faces()
        self.setup_mqtt_client()
        self.setup_camera()
        self.ensure_log_file_exists() # Novo: Garante que o arquivo de log existe

    def ensure_log_file_exists(self):
        """Garante que o arquivo de log CSV existe e tem um cabeçalho."""
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'name'])
                print(f"📄 Arquivo de log '{LOG_FILE}' criado com sucesso.")

    # ... (o restante da sua classe, métodos load_known_faces, setup_mqtt_client, etc., permanecem os mesmos)
    def load_known_faces(self):
        """Carrega os rostos conhecidos a partir do diretório de imagens."""
        print(f"🔄 Carregando rostos conhecidos da pasta '{KNOWN_FACES_DIR}'...")
        if not os.path.exists(KNOWN_FACES_DIR):
            print(f"❌ Erro: Diretório '{KNOWN_FACES_DIR}' não encontrado.")
            exit()
            
        for filename in os.listdir(KNOWN_FACES_DIR):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                name = os.path.splitext(filename)[0]
                image_path = os.path.join(KNOWN_FACES_DIR, filename)
                
                try:
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if encodings:
                        self.known_face_encodings.append(encodings[0])
                        self.known_face_names.append(name.replace('_', ' ').title())
                        print(f"✅ Rosto de '{name}' carregado com sucesso.")
                    else:
                        print(f"⚠️ Aviso: Nenhum rosto encontrado em '{filename}'.")
                except Exception as e:
                    print(f"❌ Erro ao carregar '{filename}': {e}")
        
        if not self.known_face_encodings:
            print("❗ Nenhum rosto válido foi carregado. A aplicação será encerrada.")
            exit()
        
        print(f"🎉 Carregamento concluído. Total de rostos: {len(self.known_face_names)}")
        
    def setup_mqtt_client(self):
        """Configura e conecta o cliente MQTT."""
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.on_connect = self.on_connect_callback
        
        try:
            self.client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"❌ Erro de conexão MQTT: {e}")
            exit()

    def on_connect_callback(self, client, userdata, flags, rc):
        """Callback chamado quando o cliente MQTT se conecta."""
        if rc == 0:
            print("✅ Conectado ao broker MQTT!")
            self.publish_discovery_payload()
        else:
            print(f"❌ Falha na conexão MQTT. Código: {rc}")

    def publish_discovery_payload(self):
        """Publica a mensagem de descoberta para o Home Assistant."""
        payload = json.dumps({
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
        })
        self.client.publish(MQTT_TOPIC_DISCOVERY, payload, retain=True)
        print("🚀 Payload de descoberta publicado!")

    def setup_camera(self):
        """Tenta abrir a câmera."""
        print("🎥 Abrindo a câmera...")
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            print("❌ Erro: Não foi possível abrir a câmera. Verifique as conexões.")
            exit()
        print("✅ Câmera aberta com sucesso.")

    # Novo: Método para registrar o evento no arquivo CSV
    def log_recognition_event(self, name):
        """Registra o nome, a data e a hora no arquivo de log CSV."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, name])
        print(f"✍️ Log registrado: {timestamp} - {name}")

    def run(self):
        """Loop principal da aplicação para processamento de vídeo."""
        try:
            while True:
                start_time = time.time()
                ret, frame = self.video_capture.read()
                if not ret:
                    print("⚠️ Não foi possível ler o frame da câmera. Tentando novamente...")
                    continue

                scale_factor = 0.25
                small_frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                current_recognized_name = "Nenhum Rosto Detectado"
                
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    name = "Desconhecido"
                    box_color = (0, 0, 255)

                    if True in matches:
                        first_match_index = matches.index(True)
                        name = self.known_face_names[first_match_index]
                        box_color = (0, 255, 0)
                        current_recognized_name = name

                    top = int(top / scale_factor)
                    right = int(right / scale_factor)
                    bottom = int(bottom / scale_factor)
                    left = int(left / scale_factor)

                    cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (255, 255, 255), 2)

                if current_recognized_name != self.last_recognized_name:
                    # Publica no MQTT e LOGS!
                    self.client.publish(MQTT_TOPIC_STATE, current_recognized_name)
                    print(f"📦 MQTT: Publicando '{current_recognized_name}' no tópico '{MQTT_TOPIC_STATE}'")
                    
                    # Chamada para o NOVO método de log
                    self.log_recognition_event(current_recognized_name) 
                    
                    self.last_recognized_name = current_recognized_name

                fps = 1.0 / (time.time() - start_time)
                cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                cv2.imshow('Reconhecimento Facial', frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            self.shutdown()

    def shutdown(self):
        """Libera os recursos da câmera e desconecta o cliente MQTT."""
        print("👋 Encerrando a aplicação...")
        if hasattr(self, 'video_capture') and self.video_capture.isOpened():
            self.video_capture.release()
            print("✅ Câmera liberada.")
        cv2.destroyAllWindows()
        if hasattr(self, 'client'):
            self.client.loop_stop()
            self.client.disconnect()
            print("✅ Cliente MQTT desconectado.")

# ====================================================================
# --- 3. PONTO DE ENTRADA DO SCRIPT ---
# ====================================================================

if __name__ == "__main__":
    app = FaceRecognitionApp()
    app.run()