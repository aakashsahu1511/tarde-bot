import logging
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

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


def _get_settings_or_500() -> Settings:
    try:
        return Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        logger.exception("Settings validation failed: %s", exc)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing required Kite settings (KITE_API_KEY, KITE_API_SECRET). Please configure environment variables.",
        ) from exc


def _process_request_token(settings: Settings, request_token: str, action: str | None = None) -> dict:
    try:
        from kiteconnect import KiteConnect
    except ImportError as exc:
        logger.exception("Failed to import KiteConnect library when exchanging token")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="KiteConnect SDK is not installed",
        ) from exc

    kite = KiteConnect(api_key=settings.kite_api_key)

    try:
        session_data = kite.generate_session(request_token=request_token, api_secret=settings.kite_api_secret)
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
        access_token = session_data.get("access_token", "")
        masked = (
            f"{access_token[:4]}...{access_token[-4:]}" if isinstance(access_token, str) and len(access_token) > 8 else "(redacted)"
        )
        logger.info(
            "Successfully generated Kite session for user_id=%s; access_token=%s; saved_to_env=%s",
            session_data.get("user_id"),
            masked,
            env_path,
        )
    else:
        logger.info("Kite session generated but not saved to env; session_keys=%s", list(session_data.keys()) if isinstance(session_data, dict) else None)

    return {"status": "success", "kite_session": session_data, "redirect_action": action}


@router.get("/kite/auth/login", tags=["kite"])
def kite_auth_login(
    action: str | None = Query(None, description="Optional action to preserve in redirect_params"),
    status: str | None = Query(None),
    request_token: str | None = Query(None),
    error_type: str | None = Query(None),
    error_message: str | None = Query(None),
) -> Any:
    """Start Kite login or handle a misconfigured redirect that posts back to this URL.

    If Kite redirects to this endpoint (with `status` and `request_token`), process the
    request_token the same way as `/kite/auth/callback` so the app is tolerant to misconfigured
    redirect URLs in the Kite developer console.
    """
    logger.info("/kite/auth/login endpoint hit; action=%s status=%s request_token_present=%s", action, status, bool(request_token))

    # If Kite redirected here with a request_token, handle it as a callback.
    if status and request_token:
        settings = _get_settings_or_500()
        if status.lower() != "success":
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail={"status": status, "error_type": error_type, "error_message": error_message},
            )

        return _process_request_token(settings, request_token, action)

    # Otherwise initiate a fresh login redirect
    settings = _get_settings_or_500()

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
    logger.info("Redirecting user to Kite login URL: %s", login_url)
    if action:
        redirect_params = quote_plus(f"action={action}")
        login_url = f"{login_url}&redirect_params={redirect_params}"
    return RedirectResponse(login_url)


@router.get("/kite/auth/status", tags=["kite"])
def kite_auth_status() -> dict:
    settings = Settings()  # type: ignore[call-arg]
    logger.info("/kite/auth/status endpoint hit")
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
    logger.info(
        "/kite/auth/callback endpoint hit; status=%s request_token_present=%s action=%s",
        status,
        bool(request_token),
        action,
    )

    settings = _get_settings_or_500()

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

    return _process_request_token(settings, request_token, action)


