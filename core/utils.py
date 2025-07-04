# utils.py

import cv2  # Biblioteca OpenCV para manipulação e desenho em imagens

def draw_face_box(frame, name, location, scale=1/0.25):
    """
    Desenha um retângulo ao redor do rosto detectado e escreve o nome associado.
    
    Parâmetros:
    - frame: imagem (frame) onde o desenho será feito
    - name: nome da pessoa reconhecida (string)
    - location: tupla com a posição do rosto na imagem (top, right, bottom, left)
    - scale: fator para ajustar as coordenadas da caixa (padrão é 1/0.25 porque o reconhecimento usa frame redimensionado)
    
    Retorna:
    - frame com o retângulo e nome desenhados
    """

    # Se não houver localização (nenhum rosto detectado), retorna o frame original sem alterações
    if location is None:
        return frame

    # Descompacta as coordenadas da caixa delimitadora do rosto
    top, right, bottom, left = location

    # Ajusta as coordenadas pela escala (para voltar ao tamanho original do frame)
    top = int(top * scale)
    right = int(right * scale)
    bottom = int(bottom * scale)
    left = int(left * scale)

    # Define a cor do retângulo e do texto:
    # Verde para rosto conhecido, vermelho para "Desconhecido"
    color = (0, 255, 0) if name != "Desconhecido" else (0, 0, 255)

    # Desenha o retângulo ao redor do rosto no frame
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

    # Escreve o nome acima do retângulo
    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    # Retorna o frame modificado
    return frame
