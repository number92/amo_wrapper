from fastapi import HTTPException, Query, status


from core.config import API_KEY


def verify_api_key(api_key: str = Query(None)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid query parameter API key",
        )
    return api_key
