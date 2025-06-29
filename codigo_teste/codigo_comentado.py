# Importa bibliotecas necessárias
import cv2                          # OpenCV para captura e exibição de vídeo
import face_recognition             # Biblioteca para reconhecimento facial baseada em dlib
import numpy as np                  # Biblioteca para operações com arrays (não usada diretamente aqui, mas comum em projetos com OpenCV)
import time                         # Para medir o tempo e calcular FPS (frames por segundo)

# === FASE 1: CARREGAMENTO E PREPARAÇÃO DA IMAGEM CONHECIDA ===

# Carrega a imagem da pessoa conhecida (deve conter apenas um rosto bem visível)
image_known = face_recognition.load_image_file("known_person.jpeg")

# Extrai as codificações (encodings) faciais da imagem
# face_encodings retorna uma lista de vetores de características dos rostos detectados
encodings = face_recognition.face_encodings(image_known)

# Verifica se algum rosto foi encontrado na imagem
if len(encodings) == 0:
    print("❌ Nenhum rosto detectado na imagem conhecida. Verifique a imagem.")
    exit()  # Encerra o programa se não encontrar nenhum rosto

# Armazena a codificação facial da pessoa conhecida
encoding_known = encodings[0]

# === FASE 2: INICIALIZAÇÃO DA CAPTURA DE VÍDEO ===

# Inicializa a captura de vídeo pela webcam padrão (índice 0)
video_capture = cv2.VideoCapture(0)

# Lista de codificações faciais conhecidas (pode conter várias pessoas)
known_face_encodings = [encoding_known]

# Lista de nomes correspondentes às codificações
known_face_names = ["Pessoa Conhecida"]

# === FASE 3: LOOP PRINCIPAL DE DETECÇÃO E RECONHECIMENTO ===

while True:
    # Marca o tempo de início para cálculo de FPS
    start_time = time.time()

    # Captura um frame da webcam
    ret, frame = video_capture.read()
    if not ret:
        break  # Sai do loop se não conseguir capturar imagem

    # Reduz o tamanho do frame para acelerar o processamento (1/4 do tamanho original)
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Converte o frame de BGR (formato padrão do OpenCV) para RGB (requerido pela face_recognition)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    # Localiza os rostos presentes no frame reduzido
    face_locations = face_recognition.face_locations(rgb_small_frame)

    # Gera os encodings faciais com base nas localizações detectadas
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    # Percorre todos os rostos detectados no frame
    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        # Compara cada rosto detectado com os rostos conhecidos
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

        # Define o nome padrão como "Desconhecido"
        name = "Desconhecido"

        # Se houver pelo menos uma correspondência
        if True in matches:
            # Pega o índice da primeira correspondência positiva
            first_match_index = matches.index(True)
            # Usa o nome correspondente ao encoding conhecido
            name = known_face_names[first_match_index]

        # Ajusta as coordenadas de volta ao tamanho original do frame (multiplica por 4)
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Desenha um retângulo ao redor do rosto detectado
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Escreve o nome identificado acima do retângulo
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (255, 255, 255), 2)

    # Calcula o FPS com base no tempo decorrido
    fps = 1.0 / (time.time() - start_time)

    # Mostra o FPS no canto superior esquerdo do frame
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Exibe o frame com os resultados em uma janela chamada "Video"
    cv2.imshow('Video', frame)

    # Sai do loop se a tecla 'q' for pressionada
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# === FASE FINAL: LIBERAÇÃO DE RECURSOS ===

# Encerra a captura de vídeo
video_capture.release()

# Fecha todas as janelas abertas do OpenCV
cv2.destroyAllWindows()
