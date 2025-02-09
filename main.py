import asyncio
import pprint
from core.amohelper import AMOClient
from core.config import AMO_LONG_TOKEN, AMO_PREFIX, DATE_TO, DATE_FROM
import datetime

amoclient = AMOClient(AMO_PREFIX, AMO_LONG_TOKEN)


async def main():
    date_from = amoclient.date_to_timestamp(DATE_FROM)
    date_to = amoclient.date_to_timestamp(DATE_TO)
    leads = await amoclient.get_leads_with_loss_reason(
        filters={"created_at__from": date_from, "created_at__to": date_to}
    )
    # pipelines = await amoclient.get_pipelines()
    # contacts = await amoclient.get_contacts()
    # pprint.pprint(leads["_page"])
    # pprint.pprint(leads["_links"])

    pprint.pprint(leads["_embedded"]["leads"][-1])


if __name__ == "__main__":
    asyncio.run(main())

# TODO:
# сделать обход пагинации с ожиданием
# нужно сделать статусы в сделки в строке,
# собрать все кастомные поля, для дф
#
