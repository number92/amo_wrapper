from fastapi import FastAPI

from router.amowebhook import router
from core.logger import get_logger

logger = get_logger()

app = FastAPI()
app.include_router(router)
logger.info("Запуск приложения 🐍")
