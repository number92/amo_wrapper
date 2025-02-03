import asyncio
import pprint
from core.amohelper import AMOClient
from core.config import AMO_LONG_TOKEN, AMO_PREFIX

amoclient = AMOClient(AMO_PREFIX, AMO_LONG_TOKEN)


async def main():
    result = await amoclient.get_leads()
    pprint.pprint(result["_page"])
    pprint.pprint(result["_links"])

    pprint.pprint(result["_embedded"]["leads"][-1])


if __name__ == "__main__":
    asyncio.run(main())
