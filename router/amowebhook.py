import json
import logging
from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from urllib.parse import parse_qs

from core.dependencies import verify_api_key
from core.logger import get_logger
from core.config import DEV_MODE

router = APIRouter(prefix="/wh/amo-integrations")
logger = get_logger(level=logging.DEBUG)

if not DEV_MODE:
    router.dependencies = [Depends(verify_api_key)]


def decode_urlencoded(data: bytes) -> dict:
    """Декодирует данные из формата application/x-www-form-urlencoded в словарь."""
    decoded_data = data.decode()
    parsed_data = parse_qs(decoded_data)

    # Преобразуем значения в parsed_data в нужный формат
    return {key: value[0] for key, value in parsed_data.items()}


@router.post("/newlead")
async def handle_newLead(request: Request):
    request_body = await request.body()

    request_body_json = decode_urlencoded(request_body)

    request_data = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "path_params": dict(request.path_params),
        "request_body": request_body_json,
    }
    logger.debug(request_data)
    logger.info("Received data: %s", request_body_json)

    return JSONResponse(content={}, status_code=status.HTTP_200_OK)


async def handle_update_lead(request: Request): ...


async def hande_update_status_lead(request: Request): ...
