# logger.py

import csv
import os
from datetime import datetime
from config import LOG_FILE

class Logger:
    def __init__(self):
        if not os.path.exists(LOG_FILE):
            with open(LOG_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "name"])

    def log(self, name):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, name])
        print(f"✍️ {timestamp} - {name}")
