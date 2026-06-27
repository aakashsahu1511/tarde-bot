from hashlib import sha256
import logging
from typing import Optional
import logging
import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.config import settings
from app.schemas import TokenResponse


from app.config import Settings, settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/kite/auth/login", tags=["kite"])
async def auth(
    request_token: Optional[str] = Query(
        None,
        description="Request token returned from Kite after successful login",
    ),
    status: Optional[str] = Query(None, description="Optional authentication status from Kite"),
    redirect_params: Optional[str] = Query(
        None,
        description="Optional URL-encoded redirect params",
    ),
):
    if request_token:
        if status and status.lower() != "success":
            raise HTTPException(
                status_code=400,
                detail={"error": "authentication_failed", "status": status},
            )

        checksum_input = f"{settings.kite_api_key}{request_token}{settings.kite_api_secret}"
        checksum = sha256(checksum_input.encode("utf-8")).hexdigest()

        token_url = f"{settings.kite_base_url}/session/token"
        payload = {
            "api_key": settings.kite_api_key,
            "request_token": request_token,
            "checksum": checksum,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(token_url, data=payload)

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "kite_token_exchange_failed",
                    "status_code": response.status_code,
                    "response": response.text,
                },
            )

        data = response.json()
        if "access_token" not in data:
            raise HTTPException(
                status_code=502,
                detail={
                    "error": "kite_response_invalid",
                    "response": data,
                },
            )

        token = TokenResponse(**data)
        return JSONResponse(
            status_code=200,
            content={"message": "Authentication successful", "token": token.dict(exclude_none=True)},
        )

    base_url = "https://kite.zerodha.com/connect/login"
    query = f"?v=3&api_key={settings.kite_api_key}"
    if redirect_params:
        query += f"&redirect_params={redirect_params}"

    return {
        "login_url": f"{base_url}{query}",
        "redirect_url": str(settings.kite_redirect_url),
    }

