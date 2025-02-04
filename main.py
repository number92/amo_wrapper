import asyncio
import pprint
from core.amohelper import AMOClient
from core.config import AMO_LONG_TOKEN, AMO_PREFIX

amoclient = AMOClient(AMO_PREFIX, AMO_LONG_TOKEN)


async def main():
    # leads = await amoclient.get_leads()
    # pipelines = await amoclient.get_pipelines()
    contacts = await amoclient.get_contacts()
    # pprint.pprint(leads["_page"])
    # pprint.pprint(leads["_links"])

    pprint.pprint(contacts["_embedded"]["leads"][-1])


if __name__ == "__main__":
    asyncio.run(main())
