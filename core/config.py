import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv()

AMO_PREFIX = "mitumoscow"
AMO_LONG_TOKEN = os.getenv("AMO_LONG_TOKEN")
DATE_TODAY = datetime.now().date().strftime("%d.%m.%Y")
DATE_FROM = "01.01.2025"

ALIAS_MAPPING = {
    "ID": "id",
    "Название сделки": "name",
    "Этап сделки": "stage",
    "Воронка": "pipeline",
    "Бюджет": "price",
    "Причина отказа": "loss_reason",
    "Дата создания": "created_at",
    "Дата закрытия": "closed_at",
    "Ответственный": "responsible_user",
    "Вид": "view",
    "Институт": "institute",
    "Поступление": "admission",
    "Тип программы": "program_type",
    "Направление(1)": "direction_1",
    "Осн. Профиль": "main_profile",
    "Доп. профиль МИТУ": "additional_profile_mitu",
    "Направление ДПО": "dpo_direction",
    "Программа ДПО": "dpo_program",
    "Часы ДПО": "dpo_hours",
    "Кол.мес": "months_count",
    "Причина отказа (осн)": "refusal_reason",
    "Google Client ID": "google_client_id",
    "Источник рекламы": "advertising_source",
    "Тип трафика": "traffic_type",
    "Название РК": "campaign_name",
    "Объявление": "advertisement",
    "Ключевое слово": "keyword",
    "ym_uid": "ym_uid",
    "ym_counter": "ym_counter",
}

ALIAS_REVERT = {
    "id": "ID",
    "name": "Название сделки",
    "stage": "Этап сделки",
    "pipeline": "Воронка",
    "price": "Бюджет",
    "loss_reason": "Причина отказа",
    "created_at": "Дата создания",
    "closed_at": "Дата закрытия",
    "responsible_user": "Ответственный",
    "view": "Вид",
    "institute": "Институт",
    "admission": "Поступление",
    "program_type": "Тип программы",
    "direction_1": "Направление(1)",
    "main_profile": "Осн. Профиль",
    "additional_profile_mitu": "Доп. профиль МИТУ",
    "dpo_direction": "Направление ДПО",
    "dpo_program": "Программа ДПО",
    "dpo_hours": "Часы ДПО",
    "months_count": "Кол.мес",
    "refusal_reason": "Причина отказа (осн)",
    "google_client_id": "Google Client ID",
    "advertising_source": "Источник рекламы",
    "traffic_type": "Тип трафика",
    "campaign_name": "Название РК",
    "advertisement": "Объявление",
    "keyword": "Ключевое слово",
    "ym_uid": "YM UID",
    "ym_counter": "YM Counter",
    # Добавьте новые поля здесь
}
