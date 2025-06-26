import cv2
import face_recognition
import numpy as np
import time

# Carregar imagem da pessoa conhecida
image_known = face_recognition.load_image_file("known_person.jpeg")
encodings = face_recognition.face_encodings(image_known)

if len(encodings) == 0:
    print("❌ Nenhum rosto detectado na imagem conhecida. Verifique a imagem.")
    exit()

encoding_known = encodings[0]

# Inicializar captura de vídeo da webcam do notebook
video_capture = cv2.VideoCapture(0)

known_face_encodings = [encoding_known]
known_face_names = ["Pessoa Conhecida"]

while True:
    start_time = time.time()
    ret, frame = video_capture.read()
    if not ret:
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # --- Alteração crucial aqui, conforme a solução do GitHub ---
    # Converte o frame de BGR para RGB para garantir a compatibilidade com o dlib
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    
    # 1. Detecta as localizações dos rostos
    face_locations = face_recognition.face_locations(rgb_small_frame)

    # 2. Calcula os encodings usando as localizações detectadas
    # A função `face_encodings` agora recebe as localizações
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
    
    # --- Fim da alteração do código ---

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
        name = "Desconhecido"

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]

        # Redimensiona para coordenadas originais
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.9, (255, 255, 255), 2)

    fps = 1.0 / (time.time() - start_time)
    cv2.putText(frame, f"FPS: {fps:.2f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

video_capture.release()
cv2.destroyAllWindows()