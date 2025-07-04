# face_recognition_module.py

""" 
Esse módulo é a base do sistema de reconhecimento facial, sendo usado normalmente junto com captura de vídeo em tempo real (como na classe Camera). Se quiser, posso te mostrar como integrá-lo com um sistema de notificação, abertura de porta ou registro de log.
"""

import face_recognition  # Biblioteca principal usada para detecção e reconhecimento facial
import os                # Usada para manipulação de arquivos e diretórios
from config import KNOWN_FACES_DIR  # Caminho para a pasta com imagens de rostos conhecidos (definido no config.py)
import cv2               # Biblioteca OpenCV para processamento de imagem

class FaceRecognitionModule:
    def __init__(self):
        # Lista que armazenará os vetores de características (encodings) dos rostos conhecidos
        self.known_encodings = []

        # Lista com os nomes associados a cada encoding conhecido
        self.known_names = []

        # Carrega os rostos conhecidos da pasta especificada
        self.load_faces()

    def load_faces(self):
        """
        Carrega os rostos conhecidos a partir dos arquivos de imagem encontrados no diretório KNOWN_FACES_DIR.
        Extrai os encodings de cada rosto e armazena junto ao nome da pessoa (baseado no nome do arquivo).
        """
        print(f"🔄 Carregando rostos conhecidos de '{KNOWN_FACES_DIR}'...")

        # Verifica se a pasta existe
        if not os.path.exists(KNOWN_FACES_DIR):
            raise Exception(f"❌ Pasta '{KNOWN_FACES_DIR}' não encontrada.")

        # Percorre os arquivos da pasta
        for file in os.listdir(KNOWN_FACES_DIR):
            # Verifica se o arquivo é uma imagem suportada
            if file.endswith(('.jpg', '.jpeg', '.png')):
                # Extrai o nome da pessoa com base no nome do arquivo (sem extensão)
                name = os.path.splitext(file)[0]

                # Caminho completo da imagem
                path = os.path.join(KNOWN_FACES_DIR, file)

                # Carrega a imagem usando a biblioteca face_recognition
                image = face_recognition.load_image_file(path)

                # Extrai o encoding (vetor de características) do rosto presente na imagem
                encodings = face_recognition.face_encodings(image)

                if encodings:
                    # Se o rosto foi detectado, salva o encoding e o nome da pessoa
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name.replace('_', ' ').title())
                    print(f"✅ {name} carregado.")
                else:
                    # Se nenhum rosto foi detectado, emite um aviso
                    print(f"⚠️ Nenhum rosto detectado em '{file}'.")

        # Se nenhum encoding foi carregado, gera erro
        if not self.known_encodings:
            raise Exception("❗ Nenhum rosto válido foi carregado.")

    def recognize(self, frame):
        """
        Recebe um frame (imagem da câmera), redimensiona e converte para RGB.
        Detecta o rosto e compara com os rostos conhecidos.
        Retorna o nome da pessoa reconhecida (ou 'Desconhecido') e a localização do rosto no frame.
        """

        # Reduz o tamanho da imagem para acelerar o processamento (reduz para 25%)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Converte o frame de BGR (padrão OpenCV) para RGB (padrão face_recognition)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        # Detecta as localizações dos rostos no frame
        locations = face_recognition.face_locations(rgb_small_frame)

        # Extrai os encodings dos rostos detectados nas localizações encontradas
        encodings = face_recognition.face_encodings(rgb_small_frame, locations)

        # Se nenhum encoding for encontrado, retorna None
        if not encodings:
            return None, None

        # Considera apenas o primeiro rosto detectado (útil em ambientes com uma pessoa por vez)
        face_encoding = encodings[0]

        # Calcula a distância de similaridade entre o encoding detectado e todos os conhecidos
        distances = face_recognition.face_distance(self.known_encodings, face_encoding)

        # Se não houver rostos conhecidos, retorna como "Desconhecido"
        if len(distances) == 0:
            return "Desconhecido", locations[0]

        # Encontra o rosto conhecido com menor distância (mais parecido)
        best_match = min(enumerate(distances), key=lambda x: x[1])
        index, distance = best_match

        # Se a distância for menor que 0.6 (limiar), considera que houve correspondência
        if distance < 0.6:
            return self.known_names[index], locations[0]

        # Caso contrário, retorna "Desconhecido"
        return "Desconhecido", locations[0]
