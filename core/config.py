import os
from dotenv import load_dotenv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

AMO_PREFIX = "mitumoscow"
AMO_LONG_TOKEN = os.getenv("AMO_LONG_TOKEN")
