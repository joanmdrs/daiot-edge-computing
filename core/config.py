# config.py

import os        # Usado para acessar variáveis de ambiente do sistema
import time      # (Não está sendo usado diretamente neste trecho, mas pode ser usado por outros módulos que importam este config)

# ============================
# 🔌 CONFIGURAÇÃO DO MQTT
# ============================

# Endereço IP do broker MQTT que será utilizado para envio e recebimento de mensagens
MQTT_BROKER_IP = "192.168.3.127"

# Porta padrão do MQTT
MQTT_PORT = 1883

# Credenciais para autenticação no broker MQTT
MQTT_USER = "usermqtt"
MQTT_PASS = "passmqtt"

# Tópico onde o estado da aplicação será publicado (ex: "porta aberta", "rosto reconhecido", etc.)
MQTT_TOPIC_STATE = "face_recognition/status"

# Tópico para o discovery do estado no Home Assistant (integração automática)
MQTT_TOPIC_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/status/config"

# Tópico que escuta comandos de controle da porta (ex: abrir ou fechar a porta)
MQTT_TOPIC_DOOR_CONTROL = "face_recognition/door_control"

# Tópico para o discovery do comando de porta no Home Assistant
MQTT_TOPIC_DOOR_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/door_command/config"

# Tópico usado para enviar alertas quando um rosto desconhecido for detectado
MQTT_TOPIC_ALERT = "face_recognition/alert"

# Tópico de discovery para esses alertas no Home Assistant
MQTT_TOPIC_ALERT_DISCOVERY = "homeassistant/sensor/facial_recognition_cam/unknown_alert/config"

# ============================
# 😎 CONFIGURAÇÃO DO RECONHECIMENTO FACIAL
# ============================

# Diretório onde ficam armazenadas as imagens dos rostos conhecidos
KNOWN_FACES_DIR = "known_faces"

# Diretório onde serão salvas imagens de rostos desconhecidos capturados
UNKNOWN_FACES_DIR = "unknown_faces"

# Tolerância de reconhecimento facial: quanto menor, mais rigorosa a verificação (0.6 é um valor comum)
FACE_TOLERANCE = 0.6

# Fator de escala para reduzir o tamanho do frame (acelera o processamento, pois a imagem é menor)
SCALE_FACTOR = 0.25

# ============================
# ⏱️ CONTROLE DE TEMPO E INATIVIDADE
# ============================

# Quantidade de frames consecutivos que precisam reconhecer um rosto para confirmar a identidade
CONFIRMATION_THRESHOLD = 5

# Tempo de inatividade (em segundos) antes de considerar que a câmera não está mais detectando ninguém
INACTIVITY_TIMEOUT_SECONDS = 30

# ============================
# 📝 LOGS
# ============================

# Nome do arquivo CSV onde será registrado o histórico de reconhecimentos
LOG_FILE = "recognition_history.csv"

# ============================
# 🗃️ BANCO DE DADOS
# ============================

# URL de conexão com o banco de dados. Tenta obter da variável de ambiente DATABASE_URL, caso contrário usa SQLite local.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///recognition.db")

# ============================
# 🎥 CÂMERA
# ============================

# Índice da câmera a ser usada: 0 geralmente é a webcam padrão. 
# Também pode ser uma URL de stream de vídeo (ex: IP Webcam do celular).
CAMERA_INDEX = 1


# ============================
# 🚨 SEGURANÇA
# ============================

# Tempo mínimo (em segundos) entre dois alertas consecutivos de rosto desconhecido
ALERT_INTERVAL_SECONDS = 10
