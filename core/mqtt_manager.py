# mqtt_manager.py

import json                       # Para converter dados Python em JSON e vice-versa
import paho.mqtt.client as mqtt   # Biblioteca cliente MQTT para comunicação com broker MQTT
from config import *              # Importa todas as configurações do arquivo config.py (ex: MQTT_USER, MQTT_PASS, tópicos, IP, porta)

class MQTTManager:
    def __init__(self):
        print("🔌 Conectando ao broker MQTT...")

        # Cria uma instância do cliente MQTT
        self.client = mqtt.Client()

        # Configura as credenciais de usuário e senha para autenticação no broker MQTT
        self.client.username_pw_set(MQTT_USER, MQTT_PASS)

        # Define a função que será chamada quando a conexão for estabelecida
        self.client.on_connect = self.on_connect

        # Conecta ao broker MQTT usando IP, porta e keepalive de 60 segundos
        self.client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)

        # Inicia o loop de rede em uma thread separada para processar mensagens de forma assíncrona
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        """
        Callback executado quando a conexão com o broker MQTT é estabelecida.
        Parâmetros:
        - client: o cliente MQTT
        - userdata: dados definidos pelo usuário (não usado aqui)
        - flags: bandeiras da conexão
        - rc: código de resultado da conexão (0 = sucesso)
        """
        if rc == 0:
            print("✅ Conectado ao broker MQTT.")
            # Publica mensagens de descoberta para integração com Home Assistant
            self.publish_discovery()
        else:
            print(f"❌ Falha na conexão MQTT. Código: {rc}")

    def publish_discovery(self):
        """
        Publica mensagens MQTT de descoberta (discovery) para o Home Assistant.
        Essas mensagens permitem que o Home Assistant detecte automaticamente os sensores e comandos.
        """

        # Publica a configuração do sensor do último rosto reconhecido
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

        # Publica a configuração do sensor/status do comando da porta
        self.publish(MQTT_TOPIC_DOOR_DISCOVERY, json.dumps({
            "name": "Status da Porta",
            "state_topic": MQTT_TOPIC_DOOR_CONTROL,
            "unique_id": "face_recognition_cam_door_command",
            "value_template": "{% if value_json.command == 'open' %}Aberta{% else %}Fechada{% endif %}",
            "icon": "mdi:door",
            "json_attributes_topic": MQTT_TOPIC_DOOR_CONTROL,
            "device": {
                "identifiers": ["facial_recognition_cam_01"]
            }
        }), retain=True)

        # Publica a configuração do sensor para alertas de rostos desconhecidos
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
        """
        Publica uma mensagem no broker MQTT.

        Parâmetros:
        - topic: tópico MQTT onde a mensagem será publicada
        - payload: conteúdo da mensagem (string, geralmente JSON)
        - retain: se True, a mensagem fica retida no broker para novos assinantes
        """
        self.client.publish(topic, payload, retain=retain)

    def disconnect(self):
        """
        Desconecta o cliente MQTT e para o loop de rede.
        """
        self.client.loop_stop()
        self.client.disconnect()
        print("✅ Cliente MQTT desconectado.")
