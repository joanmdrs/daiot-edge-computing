import cv2
import face_recognition
import numpy as np
import time
import os
import paho.mqtt.client as mqtt
import json
import csv
from datetime import datetime
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

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

# Configuração do arquivo de log
LOG_FILE = "recognition_history.csv"

# ====================================================================
# --- 2. CLASSE DA LÓGICA DE RECONHECIMENTO (BACKEND) ---
# ====================================================================

class FaceRecognitionBackend:
    """Gerencia a lógica de reconhecimento facial e comunicação MQTT."""
    def __init__(self, update_gui_callback):
        self.update_gui_callback = update_gui_callback
        self.running = False
        self.known_face_encodings = []
        self.known_face_names = []
        self.last_recognized_name = None
        self.video_capture = None
        self.client = None
        self.current_frame = None

        self.load_known_faces()
        self.ensure_log_file_exists()
        self.setup_mqtt_client()
        
    def load_known_faces(self):
        """Carrega os rostos conhecidos a partir do diretório de imagens."""
        print(f"🔄 Carregando rostos conhecidos da pasta '{KNOWN_FACES_DIR}'...")
        if not os.path.exists(KNOWN_FACES_DIR):
            print(f"❌ Erro: Diretório '{KNOWN_FACES_DIR}' não encontrado.")
            return
            
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
                        print(f"✅ Rosto de '{name}' carregado.")
                    else:
                        print(f"⚠️ Aviso: Nenhum rosto encontrado em '{filename}'.")
                except Exception as e:
                    print(f"❌ Erro ao carregar '{filename}': {e}")
        
        if not self.known_face_encodings:
            print("❗ Nenhum rosto válido foi carregado.")
        else:
            print(f"🎉 Carregamento concluído. Total: {len(self.known_face_names)}")
    
    def ensure_log_file_exists(self):
        """Garante que o arquivo de log CSV existe e tem um cabeçalho."""
        if not os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, mode='w', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow(['timestamp', 'name'])
                    print(f"📄 Arquivo de log '{LOG_FILE}' criado.")
            except PermissionError:
                print(f"❌ Erro de Permissão: Não foi possível criar/escrever em '{LOG_FILE}'. O arquivo pode estar aberto ou você precisa de permissões de Administrador.")
                # Não saia do programa, apenas desative o log
                self.log_recognition_event = lambda name: None 

    def log_recognition_event(self, name):
        """Registra o nome, a data e a hora no arquivo de log CSV."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, name])
        print(f"✍️ Log registrado: {timestamp} - {name}")

    def setup_mqtt_client(self):
        """Configura e conecta o cliente MQTT."""
        # CORREÇÃO: Usando a versão de API 2 para evitar o aviso de depreciação
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        self.client.on_connect = self.on_connect_callback
        try:
            self.client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"❌ Erro de conexão MQTT: {e}")
            self.update_gui_callback("status_update", "❌ Erro de conexão MQTT!", "red")

    def on_connect_callback(self, client, userdata, flags, rc):
        """Callback chamado quando o cliente MQTT se conecta."""
        if rc == 0:
            print("✅ Conectado ao broker MQTT!")
            self.publish_discovery_payload()
            # CORREÇÃO: A atualização da GUI é agendada para a thread principal
            self.update_gui_callback("status_update", "✅ Conectado ao MQTT!", "green")
        else:
            print(f"❌ Falha na conexão MQTT. Código: {rc}")
            self.update_gui_callback("status_update", f"❌ Falha MQTT ({rc})", "red")

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
    
    def start_camera(self):
        """Tenta abrir a câmera."""
        print("🎥 Abrindo a câmera...")
        self.video_capture = cv2.VideoCapture(0)
        if not self.video_capture.isOpened():
            print("❌ Erro: Não foi possível abrir a câmera. Verifique as conexões.")
            self.update_gui_callback("status_update", "❌ Erro na Câmera!", "red")
            return False
        print("✅ Câmera aberta com sucesso.")
        self.running = True
        return True

    def stop_camera(self):
        """Para o loop de vídeo e libera a câmera."""
        self.running = False
        if self.video_capture is not None and self.video_capture.isOpened():
            self.video_capture.release()
            print("✅ Câmera liberada.")
        self.update_gui_callback("status_update", "🔴 Parado", "red")
        
    def video_loop(self):
        """Loop de processamento de vídeo em um thread separado."""
        if not self.start_camera():
            return

        self.update_gui_callback("status_update", "🟢 Rodando", "green")
        self.update_gui_callback("name_update", "Aguardando reconhecimento...")

        while self.running:
            ret, frame = self.video_capture.read()
            if not ret:
                print("⚠️ Não foi possível ler o frame da câmera. Tentando novamente...")
                continue
            
            # Atualiza o frame para a GUI
            self.current_frame = frame.copy()

            # Processamento de reconhecimento
            scale_factor = 0.25
            small_frame = cv2.resize(frame, (0, 0), fx=scale_factor, fy=scale_factor)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            current_recognized_name = "Nenhum Rosto Detectado"
            
            for _, face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                if True in matches:
                    first_match_index = matches.index(True)
                    current_recognized_name = self.known_face_names[first_match_index]
                    break
                else:
                    current_recognized_name = "Desconhecido"

            if current_recognized_name != self.last_recognized_name:
                self.client.publish(MQTT_TOPIC_STATE, current_recognized_name)
                print(f"📦 MQTT: Publicando '{current_recognized_name}'")
                
                # Chamada para o método de log
                self.log_recognition_event(current_recognized_name) 
                
                self.last_recognized_name = current_recognized_name
                self.update_gui_callback("name_update", f"Reconhecido: {current_recognized_name}")

        self.stop_camera()

    def shutdown(self):
        """Libera os recursos da câmera e desconecta o cliente MQTT."""
        print("👋 Encerrando a aplicação...")
        self.stop_camera()
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("✅ Cliente MQTT desconectado.")


# ====================================================================
# --- 3. CLASSE DA INTERFACE GRÁFICA (FRONTEND) ---
# ====================================================================

class FaceRecognitionGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Reconhecimento Facial")
        self.geometry("800x600")
        
        # Cria a instância do backend e passa o callback para a GUI
        self.backend = FaceRecognitionBackend(self.update_gui)
        
        self.create_widgets()
        self.camera_thread = None
        self.update_frame_display()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_widgets(self):
        # Frame de controle
        control_frame = ttk.Frame(self, padding="10")
        control_frame.pack(fill=tk.X)
        
        self.start_button = ttk.Button(control_frame, text="Iniciar Reconhecimento", command=self.start_recognition)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.stop_button = ttk.Button(control_frame, text="Parar", command=self.stop_recognition, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.status_label = ttk.Label(control_frame, text="🔴 Aguardando Iniciar", font=("Helvetica", 12))
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Label para mostrar o status do reconhecimento
        self.name_label = ttk.Label(self, text="Status: Pronto", font=("Helvetica", 14, "bold"), foreground="blue")
        self.name_label.pack(pady=10)

        # Label para exibir o feed da câmera
        self.video_label = tk.Label(self, bd=2, relief="sunken")
        self.video_label.pack(pady=10)

    def start_recognition(self):
        """Inicia o thread de processamento da câmera."""
        if self.camera_thread is None or not self.camera_thread.is_alive():
            self.camera_thread = threading.Thread(target=self.backend.video_loop, daemon=True)
            self.camera_thread.start()
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.name_label.config(text="Iniciando câmera...")

    def stop_recognition(self):
        """Para o thread de processamento da câmera."""
        self.backend.stop_camera()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.name_label.config(text="Status: Parado")

    def update_gui(self, action, message, color=None):
        """
        Callback para atualizar os widgets da GUI a partir do thread de backend.
        CORREÇÃO: Agenda a atualização na thread principal da GUI.
        """
        if action == "status_update":
            # Agendamos a atualização para ser executada no próximo ciclo do mainloop
            self.after(0, self.status_label.config, {'text': message, 'foreground': color})
        elif action == "name_update":
            self.after(0, self.name_label.config, {'text': message})
        
    def update_frame_display(self):
        """Atualiza a imagem exibida na label de vídeo."""
        if self.backend.current_frame is not None:
            # Converte o frame do OpenCV para um formato que o Tkinter pode exibir
            frame = cv2.cvtColor(self.backend.current_frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame)
            # Redimensiona para caber na janela
            image_tk = ImageTk.PhotoImage(image)
            self.video_label.config(image=image_tk)
            self.video_label.image = image_tk # Mantém uma referência para evitar garbage collection
        
        # Agenda a próxima atualização
        self.after(15, self.update_frame_display)

    def on_closing(self):
        """Função chamada ao fechar a janela."""
        print("Fechando a janela da aplicação.")
        self.backend.shutdown()
        self.destroy()

# ====================================================================
# --- 4. PONTO DE ENTRADA DO SCRIPT ---
# ====================================================================

if __name__ == "__main__":
    app_gui = FaceRecognitionGUI()
    app_gui.mainloop()