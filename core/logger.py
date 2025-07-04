# logger.py

import csv                       # Biblioteca para manipulação de arquivos CSV
import os                        # Biblioteca para interações com o sistema de arquivos (como verificar se um arquivo existe)
from datetime import datetime    # Importa datetime para obter data e hora atual
from config import LOG_FILE      # Importa o caminho do arquivo de log a partir do arquivo de configuração
                                 # (ex: "recognition_history.csv")

class Logger:
    def __init__(self):
        """
        Construtor da classe Logger.
        Verifica se o arquivo de log já existe.
        Caso contrário, cria o arquivo e escreve o cabeçalho (colunas).
        """
        if not os.path.exists(LOG_FILE):
            # Abre o arquivo no modo escrita ("w"), criando se não existir
            with open(LOG_FILE, "w", newline="") as f:
                writer = csv.writer(f)                      # Cria o escritor CSV
                writer.writerow(["timestamp", "name"])     # Escreve o cabeçalho com as colunas: data/hora e nome

    def log(self, name):
        """
        Registra uma entrada no arquivo de log.
        Cada entrada inclui o timestamp atual e o nome da pessoa reconhecida.

        Parâmetros:
        - name: Nome da pessoa (ou "Desconhecido")
        """
        # Gera o timestamp atual no formato YYYY-MM-DD HH:MM:SS
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Abre o arquivo no modo append ("a") para adicionar uma nova linha
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)                  # Cria o escritor CSV
            writer.writerow([timestamp, name])      # Escreve a linha com o timestamp e o nome

        # Imprime no console para feedback imediato
        print(f"✍️ {timestamp} - {name}")
