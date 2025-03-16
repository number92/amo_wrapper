import os
import csv
import logging

from core.schemes.to_table import ToCSV
from core import amoclient, config


async def lead_to_csv_file(date_from: str = config.DATE_FROM, date_to: str = config.DATE_TODAY, by_alias: bool = False):
    pipelines = await amoclient.get_pipelines()
    leads = await amoclient.get_leads(
        filters={
            "created_at__from": amoclient.date_to_timestamp(date_from),
            "created_at__to": amoclient.date_to_timestamp(date_to),
        },
        with_params=["contacts", "loss_reason"],
    )
    to_csv = ToCSV()
    to_csv.add_lead_table_to_items(pipelines, leads)

    leads_data = to_csv.model_dump(by_alias=by_alias)
    file_name = f"{config.DATE_TODAY}-leads-{to_csv.count_items}.csv"
    upload_path = config.BASE_DIR / "uploads" / file_name
    os.makedirs(upload_path.parent, exist_ok=True)
    with open(upload_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=leads_data["items"][0].keys())
        writer.writeheader()  # Записываем заголовки
        writer.writerows(leads_data["items"])
    logging.info("Данные записаны в файл %s", file_name)
