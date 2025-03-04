import asyncio
import logging

from core.schemes.to_table import ToCSV
from core.amohelper import AMOClient
from core.config import AMO_LONG_TOKEN, AMO_PREFIX, DATE_TO, DATE_FROM
import datetime

amoclient = AMOClient(AMO_PREFIX, AMO_LONG_TOKEN)


async def main():
    logging.basicConfig(level=logging.DEBUG)

    date_from = amoclient.date_to_timestamp("01.03.2025")
    date_to = amoclient.date_to_timestamp(DATE_TO)
    # leads = await amoclient.get_leads_with_params(
    #     filters={"created_at__from": date_from, "created_at__to": date_to},
    #     with_params=["contacts", "loss_reason"],
    #     limit=15,
    #     page=333,
    # )
    pipelines = await amoclient.get_pipelines()
    leads = await amoclient.get_leads(
        filters={"created_at__from": date_from, "created_at__to": date_to},
        with_params=["contacts", "loss_reason"],
    )
    to_csv = ToCSV()
    to_csv.add_lead_table_to_items(list_pipelines=pipelines, leads=leads)
    print(to_csv.model_dump(by_alias=True))
    # pipelines = await amoclient.get_pipelines()
    # TODO: сделать обертку для табличного представления


if __name__ == "__main__":
    asyncio.run(main())

# TODO:

# нужно сделать статусы в сделки в строке,
# собрать все кастомные поля, для дф
# проверить производительность
