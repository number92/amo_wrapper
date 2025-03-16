import json
import logging
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from core.logger import get_logger

router = APIRouter(prefix="/amo-integrations")
logger = get_logger(level=logging.DEBUG)


@router.post("/newlead")
async def handle_newLead(request: Request):
    request_body = await request.body()

    try:
        request_body_json = json.loads(request_body)
    except json.JSONDecodeError:
        request_body_json = request_body.decode()
    request_data = {
        "method": request.method,
        "url": str(request.url),
        "headers": dict(request.headers),
        "query_params": dict(request.query_params),
        "path_params": dict(request.path_params),
        "request_body": request_body_json,
    }
    logger.debug("Received JSON data: %s", request_data)

    return JSONResponse(content={}, status_code=status.HTTP_200_OK)
