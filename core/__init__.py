from core import config
from core.amohelper import AMOClient


amoclient = AMOClient(url_prefix=config.AMO_PREFIX, long_token=config.AMO_LONG_TOKEN)

__all__ = ("amoclient", "config")
