from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _get_env_file() -> str | None:
    """Return .env path if it exists, otherwise None (for production).
    
    In production (Render), env vars are set directly; .env won't exist.
    Locally, we load from .env for convenience.
    """
    env_file = Path(".env")
    return str(env_file) if env_file.exists() else None


class Settings(BaseSettings):
    kite_api_key: str
    kite_api_secret: str
    kite_access_token: str | None = None
    kite_user_id: str | None = None

    kite_default_product: str = Field("MIS")
    kite_default_variety: str = Field("regular")
    kite_order_validity: str = Field("DAY")
    kite_stop_loss_minimum_amount: float = Field(10.0)
    kite_stop_loss_percentage: float = Field(0.10)
    kite_redirect_url: str | None = None
    kite_auto_save_token: bool = Field(False)

    model_config = SettingsConfigDict(
        env_file=_get_env_file(),
        env_file_encoding='utf-8'
    )
