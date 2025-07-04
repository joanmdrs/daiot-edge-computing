import cv2
import face_recognition
import numpy as np
import time
import os
import paho.mqtt.client as mqtt
import json
import csv
from datetime import datetime

# ====================================================================
# --- 1. CONFIGURAÇÕES DA APLICAÇÃO ---
# ====================================================================

# Configurações MQTT
MQTT_BROKER_IP = "192.168.88.164"
MQTT_PORT = 1883
MQTT_USER = "usermqtt"
MQTT_PASS = "passmqtt"
MQTT_TOPIC_STATE = "face_recognition/status"
MQTT_TOPIC_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/status/config"
# NOVO: Tópico para controle de porta
MQTT_TOPIC_DOOR_CONTROL = "face_recognition/door_control"
# NOVO: Tópico para alertas de desconhecidos
MQTT_TOPIC_ALERT = "face_recognition/alert"
# NOVO: Tópico de descoberta para o comando da porta (para um sensor, por exemplo)
MQTT_TOPIC_DOOR_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/door_command/config"
# NOVO: Tópico de descoberta para o alerta de desconhecido
MQTT_TOPIC_ALERT_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/unknown_alert/config"


# Diretório para as imagens de pessoas conhecidas
KNOWN_FACES_DIR = "known_faces"

# Configuração do arquivo de log
LOG_FILE = "recognition_history.csv"

# NOVO: Configurações de Debouncing
CONFIRMATION_THRESHOLD = 5  # Número de frames para confirmar o reconhecimento
consecutive_frames = 0
last_confirmed_name = "Nenhum"

# NOVO: Configurações de Inatividade
INACTIVITY_TIMEOUT_SECONDS = 30  # Tempo em segundos para considerar inativo
last_recognition_time = time.time()

# Variáveis para controlar o envio único do alerta de desconhecido
alert_sent_for_current_detection = False
last_unknown_detection_time = 0

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
        self.ensure_log_file_exists()

    def ensure_log_file_exists(self):
        """Garante que o arquivo de log CSV existe e tem um cabeçalho."""
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['timestamp', 'name'])
                print(f"📄 Arquivo de log '{LOG_FILE}' criado com sucesso.")

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
            # NOVO: Publica payloads de descoberta para as novas entidades
            self.publish_door_command_discovery_payload()
            self.publish_alert_discovery_payload()
        else:
            print(f"❌ Falha na conexão MQTT. Código: {rc}")

    def publish_discovery_payload(self):
        """Publica a mensagem de descoberta para o Home Assistant (Último Rosto Reconhecido)."""
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
        print("🚀 Payload de descoberta 'Último Rosto Reconhecido' publicado!")

    def publish_door_command_discovery_payload(self):
        """Publica a mensagem de descoberta para o Home Assistant (Comando da Porta)."""
        payload = json.dumps({
            "name": "Comando Porta Reconhecimento Facial",
            "state_topic": MQTT_TOPIC_DOOR_CONTROL,
            "unique_id": "face_recognition_cam_door_command",
            "value_template": "{% if value_json.command == 'open' %}ABERTA{% else %}FECHADA{% endif %}",
            "json_attributes_topic": MQTT_TOPIC_DOOR_CONTROL,
            "icon": "mdi:door", 
            "device": {
                "identifiers": ["facial_recognition_cam_01"],
            }
        })
        self.client.publish(MQTT_TOPIC_DOOR_DISCOVERY, payload, retain=True)
        print("🚀 Payload de descoberta 'Comando Porta' publicado!")


    def publish_alert_discovery_payload(self):
        """Publica a mensagem de descoberta para o Home Assistant (Alerta de Desconhecido)."""
        # Criamos um sensor que reporta a última mensagem de alerta
        payload = json.dumps({
            "name": "Alerta Rosto Desconhecido",
            "state_topic": MQTT_TOPIC_ALERT,
            "unique_id": "face_recognition_cam_unknown_alert",
            "value_template": "{{ value_json.message }}", # Extrai a mensagem do JSON
            "json_attributes_topic": MQTT_TOPIC_ALERT, # Pega todos os atributos do JSON
            "icon": "mdi:alert",
            "device": {
                "identifiers": ["facial_recognition_cam_01"],
            }
        })
        self.client.publish(MQTT_TOPIC_ALERT_DISCOVERY, payload, retain=True)
        print("🚀 Payload de descoberta 'Alerta Desconhecido' publicado!")

    def setup_camera(self):
        """Tenta abrir a câmera."""
        print("🎥 Abrindo a câmera...")
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            print("❌ Erro: Não foi possível abrir a câmera. Verifique as conexões.")
            exit()
        print("✅ Câmera aberta com sucesso.")

    def log_recognition_event(self, name):
        """Registra o nome, a data e a hora no arquivo de log CSV."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, name])
        print(f"✍️ Log registrado: {timestamp} - {name}")
    
    def send_alert_and_save_image(self, frame):
        """Envia um alerta MQTT e salva a imagem do rosto desconhecido."""
        global last_unknown_detection_time, alert_sent_for_current_detection

        # Só envia um alerta a cada X segundos para evitar spam
        if time.time() - last_unknown_detection_time < 10 and alert_sent_for_current_detection: # Limite de 1 alerta a cada 10 segundos
            return

        # Salva a foto
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        unknown_faces_dir = "unknown_faces"
        if not os.path.exists(unknown_faces_dir):
            os.makedirs(unknown_faces_dir)
        filename = os.path.join(unknown_faces_dir, f"unknown_{timestamp_str}.jpg")
        cv2.imwrite(filename, frame)
        print(f"📸 Foto de rosto desconhecido salva em: {filename}")
        
        # Publica o alerta MQTT
        alert_payload = json.dumps({
            "message": "Rosto desconhecido detectado!",
            "timestamp": timestamp_str,
            "image_path": filename # Caminho da imagem salva no dispositivo
        })
        self.client.publish(MQTT_TOPIC_ALERT, alert_payload)
        print(f"🚨 Alerta de desconhecido enviado via MQTT para o tópico '{MQTT_TOPIC_ALERT}'")
        
        last_unknown_detection_time = time.time()
        alert_sent_for_current_detection = True


    def run(self):
        """Loop principal da aplicação para processamento de vídeo."""
        global consecutive_frames, last_confirmed_name, last_recognition_time, alert_sent_for_current_detection
        
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
                
                current_frame_name = "Nenhum Rosto Detectado"
                
                # Reseta o flag de alerta para o frame atual
                alert_sent_for_current_detection = False

                # --- Lógica de reconhecimento e desenho de caixas ---
                if face_encodings: # Se algum rosto foi detectado no frame
                    # Se múltiplos rostos forem detectados, priorizamos o primeiro ou o mais central
                    # Para este exemplo, vamos considerar o primeiro rosto detectado
                    face_encoding = face_encodings[0]
                    top, right, bottom, left = face_locations[0]

                    current_frame_name = "Desconhecido" # Assume que é desconhecido até provar o contrário
                    
                    # NOVO: Otimização com cálculo de distância
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    best_match_index = np.argmin(face_distances)
                    
                    # NOVO: Usando um limite de tolerância para o reconhecimento
                    if face_distances[best_match_index] < 0.6: # 0.6 é um bom limite, menor é mais rigoroso
                        name = self.known_face_names[best_match_index]
                        box_color = (0, 255, 0)
                        current_frame_name = name # Define o nome para o frame atual
                    else:
                        name = "Desconhecido"
                        box_color = (0, 0, 255)
                        # Se for desconhecido, o `current_frame_name` já é "Desconhecido"
                    
                    # Converte coordenadas de volta para o tamanho original
                    top = int(top / scale_factor)
                    right = int(right / scale_factor)
                    bottom = int(bottom / scale_factor)
                    left = int(left / scale_factor)

                    # Desenha o retângulo e o nome
                    cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                                0.9, (255, 255, 255), 2)
                
                # --- Lógica de Debouncing e Publicação ---
                if current_frame_name == last_confirmed_name:
                    consecutive_frames = 0 # Reinicia a contagem se o nome for o mesmo e já foi confirmado
                else:
                    if current_frame_name == self.last_recognized_name: # Se o nome atual é o mesmo que o anterior (em contagem)
                        consecutive_frames += 1
                        if consecutive_frames >= CONFIRMATION_THRESHOLD:
                            # O nome foi confirmado!
                            self.client.publish(MQTT_TOPIC_STATE, current_frame_name)
                            self.log_recognition_event(current_frame_name)
                            print(f"📦 MQTT: Publicando '{current_frame_name}' (confirmado) no tópico '{MQTT_TOPIC_STATE}'")
                            
                            # NOVO: Aciona o portão se for uma pessoa conhecida
                            if current_frame_name != "Desconhecido" and current_frame_name != "Nenhum Rosto Detectado":
                                door_payload = json.dumps({"command": "open", "user": current_frame_name})
                                self.client.publish(MQTT_TOPIC_DOOR_CONTROL, door_payload)
                                print(f"🚪 Comando de abertura de porta enviado para '{current_frame_name}' no tópico '{MQTT_TOPIC_DOOR_CONTROL}'")

                            # NOVO: Envia alerta de desconhecido se for confirmado como "Desconhecido"
                            if current_frame_name == "Desconhecido":
                                self.send_alert_and_save_image(frame)
                            
                            self.last_recognized_name = current_frame_name
                            last_confirmed_name = current_frame_name
                            consecutive_frames = 0 # Zera a contagem após a confirmação
                    else: # Se o nome atual é diferente do anterior (inicia nova contagem)
                        consecutive_frames = 1 # Inicia a contagem para um novo nome
                        self.last_recognized_name = current_frame_name # Armazena o nome que está sendo contado
                
                # --- Lógica de Detecção de Inatividade ---
                # Apenas atualiza o tempo se houver algum rosto detectado no frame
                if current_frame_name != "Nenhum Rosto Detectado":
                    last_recognition_time = time.time()
                # Verifica a inatividade apenas se o último nome confirmado não for "Nenhum Rosto Detectado"
                elif self.last_recognized_name != "Nenhum Rosto Detectado" and \
                     time.time() - last_recognition_time > INACTIVITY_TIMEOUT_SECONDS:
                    self.client.publish(MQTT_TOPIC_STATE, "Nenhum Rosto Detectado")
                    self.last_recognized_name = "Nenhum Rosto Detectado"
                    last_confirmed_name = "Nenhum Rosto Detectado" # Reseta a confirmação também
                    print("💤 Inatividade detectada. Publicando 'Nenhum Rosto Detectado'.")

                # --- Exibição na tela ---
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