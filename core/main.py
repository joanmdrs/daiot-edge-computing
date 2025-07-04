# main.py

import cv2                          # Biblioteca OpenCV para exibição de imagem e vídeo
import time                         # Para medir tempo de execução e controlar timeout
import json                         # Para montar mensagens em formato JSON (usado no MQTT)
from datetime import datetime       # Para gerar timestamps

# Módulos do sistema
from camera import Camera                               # Captura de vídeo com threading
from mqtt_manager import MQTTManager                    # Comunicação MQTT (publicar eventos e comandos)
from face_recognition_module import FaceRecognitionModule  # Reconhecimento facial
from logger import Logger                               # Registro de eventos em CSV
from config import *                                    # Configurações gerais do sistema (paths, limites, etc.)
from utils import draw_face_box                         # Desenha caixa e nome sobre o rosto reconhecido


def main():
    # Inicializa os módulos principais
    cam = Camera()                       # Gerencia a câmera
    mqtt = MQTTManager()                # Gerencia o broker MQTT
    face_module = FaceRecognitionModule()  # Responsável pelo reconhecimento facial
    logger = Logger()                   # Responsável por registrar logs

    # Variáveis de controle do reconhecimento
    last_name = None                    # Último nome detectado (não confirmado)
    confirmed_name = None               # Nome confirmado após várias detecções consecutivas
    consecutive = 0                     # Contador de confirmações consecutivas
    last_seen = time.time()             # Timestamp da última detecção de rosto

    try:
        while True:
            # Marca o tempo de início para cálculo de FPS
            start_time = time.time()

            # Captura o frame da câmera
            frame = cam.get_frame()
            if frame is None:
                continue  # Pula iteração se o frame ainda não estiver disponível

            # Tenta reconhecer o rosto presente no frame
            name, location = face_module.recognize(frame)

            # Caso não haja rosto detectado, define como "Nenhum Rosto Detectado"
            if not name:
                name = "Nenhum Rosto Detectado"

            # Se há rosto detectado, desenha a caixa no frame
            if name != "Nenhum Rosto Detectado":
                frame = draw_face_box(frame, name, location)

            # === Lógica de controle (debounce) ===
            if name == "Nenhum Rosto Detectado":
                # Se antes havia um rosto confirmado, publica ausência agora
                if confirmed_name != "Nenhum Rosto Detectado":
                    mqtt.publish(MQTT_TOPIC_STATE, "Nenhum Rosto Detectado")
                    print("💤 Nenhum rosto detectado. Atualizando estado.")
                    confirmed_name = "Nenhum Rosto Detectado"
                    last_name = None
                    consecutive = 0
            else:
                if name == confirmed_name:
                    consecutive = 0  # Já está confirmado, nada muda
                elif name == last_name:
                    consecutive += 1  # Mesmo nome detectado novamente

                    # Se atingiu o limiar de confirmação, confirma o nome
                    if consecutive >= CONFIRMATION_THRESHOLD:
                        logger.log(name)  # Registra o reconhecimento
                        mqtt.publish(MQTT_TOPIC_STATE, name)  # Publica nome reconhecido

                        if name != "Desconhecido":
                            # Se reconhecido, envia comando para abrir a porta
                            payload = json.dumps({"command": "open", "user": name})
                            mqtt.publish(MQTT_TOPIC_DOOR_CONTROL, payload)
                            print(f"🟢 LED ON - Porta aberta para {name}")
                        else:
                            # Caso desconhecido, envia alerta
                            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                            alert_payload = json.dumps({
                                "message": "Rosto desconhecido detectado!",
                                "timestamp": timestamp
                            })
                            mqtt.publish(MQTT_TOPIC_ALERT, alert_payload)
                            print("🔴 LED OFF - Acesso negado (Desconhecido)")

                        confirmed_name = name
                        consecutive = 0
                else:
                    # Novo nome detectado, reinicia contagem
                    last_name = name
                    consecutive = 1

            # Atualiza o tempo do último rosto visto
            if name != "Nenhum Rosto Detectado":
                last_seen = time.time()
            elif time.time() - last_seen > INACTIVITY_TIMEOUT_SECONDS and confirmed_name != "Nenhum Rosto Detectado":
                mqtt.publish(MQTT_TOPIC_STATE, "Nenhum Rosto Detectado")
                confirmed_name = "Nenhum Rosto Detectado"
                print("💤 Timeout de inatividade. Estado atualizado.")

            # === Exibição do FPS no frame ===
            fps = 1.0 / (time.time() - start_time)
            cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Exibe a imagem com OpenCV
            cv2.imshow("Reconhecimento Facial", frame)

            # Encerra o programa se a tecla 'q' for pressionada
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    finally:
        # Encerra recursos mesmo se ocorrer erro ou fechamento
        mqtt.disconnect()
        cam.release()
        cv2.destroyAllWindows()

# Executa o programa se este arquivo for o principal
if __name__ == "__main__":
    main()
