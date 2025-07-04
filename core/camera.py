# camera.py (com threading)

""" 
o arquivo camera.py define uma classe Camera que faz a captura de vídeo em tempo real da webcam, utilizando multithreading para que a captura de imagens ocorra continuamente em segundo plano, sem bloquear o restante do programa.
"""

import cv2                # Importa a biblioteca OpenCV para captura de vídeo e processamento de imagem
import threading          # Importa o módulo threading para executar captura em segundo plano (thread)
from config import CAMERA_INDEX  # Importa o índice da câmera a ser utilizada a partir do arquivo config.py

class Camera:
    def __init__(self):
        # Inicializa o objeto de captura de vídeo com o índice da câmera especificado
        self.video_capture = cv2.VideoCapture(CAMERA_INDEX)

        # Define a largura do frame de vídeo para 640 pixels
        self.video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)

        # Define a altura do frame de vídeo para 480 pixels
        self.video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Verifica se a câmera foi aberta corretamente
        if not self.video_capture.isOpened():
            # Lança uma exceção se não foi possível acessar a câmera
            raise Exception("❌ Erro: Não foi possível abrir a câmera.")

        # Inicializa a variável que armazenará o frame mais recente
        self.frame = None

        # Variável de controle para manter o loop de captura ativo
        self.running = True

        # Cria uma thread para capturar frames continuamente, sem travar o fluxo principal da aplicação
        self.thread = threading.Thread(target=self.update, daemon=True)

        # Inicia a execução da thread
        self.thread.start()

    def update(self):
        """
        Método executado pela thread que atualiza continuamente o frame mais recente.
        """
        while self.running:
            # Captura um frame da câmera
            ret, frame = self.video_capture.read()

            # Se a captura for bem-sucedida, atualiza o frame armazenado
            if ret:
                self.frame = frame

    def get_frame(self):
        """
        Retorna o frame mais recente capturado pela câmera.
        """
        return self.frame

    def release(self):
        """
        Libera os recursos da câmera e finaliza a thread de captura com segurança.
        """
        # Para o loop de captura
        self.running = False

        # Aguarda o término da thread de captura
        self.thread.join()

        # Libera o dispositivo da câmera
        self.video_capture.release()

        # Mensagem de confirmação
        print("✅ Câmera liberada.")
