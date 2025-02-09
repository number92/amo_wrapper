import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

AMO_PREFIX = "mitumoscow"
AMO_LONG_TOKEN = os.getenv("AMO_LONG_TOKEN")
DATE_TO = datetime.now().date().strftime("%d.%m.%Y")  # Текущая дата
DATE_FROM = "01.01.2025"
