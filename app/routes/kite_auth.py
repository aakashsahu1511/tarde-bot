import logging
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status
from fastapi.responses import RedirectResponse

from app.config import Settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _env_path(settings: Settings) -> Path:
    env_file = settings.model_config.get("env_file", ".env")
    path = Path(str(env_file))
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _update_env_file(access_token: str, user_id: str, env_path: Path) -> None:
    env_path.parent.mkdir(parents=True, exist_ok=True)
    original_lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    updated_lines = []
    found_access_token = False
    found_user_id = False

    for line in original_lines:
        if line.strip().startswith("KITE_ACCESS_TOKEN="):
            updated_lines.append(f"KITE_ACCESS_TOKEN={access_token}")
            found_access_token = True
        elif line.strip().startswith("KITE_USER_ID="):
            updated_lines.append(f"KITE_USER_ID={user_id}")
            found_user_id = True
        else:
            updated_lines.append(line)

    if not found_access_token:
        updated_lines.append(f"KITE_ACCESS_TOKEN={access_token}")
    if not found_user_id:
        updated_lines.append(f"KITE_USER_ID={user_id}")

    env_path.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")


@router.get("/kite/auth/login", tags=["kite"])
def kite_auth_login() -> RedirectResponse:
    settings = Settings()  # type: ignore[call-arg]

    try:
        from kiteconnect import KiteConnect
    except ImportError as exc:
        logger.exception("Failed to import KiteConnect library")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KiteConnect SDK is not installed",
        ) from exc

    kite = KiteConnect(api_key=settings.kite_api_key)
    login_url = kite.login_url()
    return RedirectResponse(login_url)


@router.get("/kite/auth/status", tags=["kite"])
def kite_auth_status() -> dict:
    settings = Settings()  # type: ignore[call-arg]
    authenticated = bool(settings.kite_access_token and settings.kite_user_id)
    return {
        "authenticated": authenticated,
        "kite_user_id": settings.kite_user_id,
        "saved_token": bool(settings.kite_access_token),
    }


@router.get("/kite/auth/callback", tags=["kite"])
def kite_auth_callback(
    status: str = Query(...),
    request_token: str | None = Query(None),
    action: str | None = Query(None),
    error_type: str | None = Query(None),
    error_message: str | None = Query(None),
) -> Any:
    settings = Settings()  # type: ignore[call-arg]

    if status.lower() != "success":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail={"status": status, "error_type": error_type, "error_message": error_message},
        )

    if not request_token:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Missing request_token in Kite redirect callback",
        )

    try:
        from kiteconnect import KiteConnect
    except ImportError as exc:
        logger.exception("Failed to import KiteConnect library")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KiteConnect SDK is not installed",
        ) from exc

    kite = KiteConnect(api_key=settings.kite_api_key)

    try:
        session_data = kite.generate_session(request_token, settings.kite_api_secret)
    except Exception as exc:
        logger.exception("Kite session generation failed for request token %s", request_token)
        raise HTTPException(
            status_code=http_status.HTTP_502_BAD_GATEWAY,
            detail="Failed to generate Kite session from redirect callback",
        ) from exc

    if (
        settings.kite_auto_save_token
        and isinstance(session_data, dict)
        and session_data.get("access_token")
        and session_data.get("user_id")
    ):
        env_path = _env_path(settings)
        _update_env_file(session_data["access_token"], session_data["user_id"], env_path)
        session_data["saved_to_env"] = str(env_path)

    return {
        "status": "success",
        "kite_session": session_data,
        "redirect_action": action,
    }


