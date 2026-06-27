from pathlib import Path
import logging

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def _get_env_file() -> str | None:
    """Return .env path if it exists, otherwise None (for production).
    
    Pydantic BaseSettings automatically reads process environment variables.
    In production (Render), those env vars are injected by Render and .env is not needed.
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
        env_file_encoding='utf-8',
        env_prefix="",
    )

    def log_loaded_env(self) -> None:
        logger.info(
            "Loaded Kite settings from env: KITE_API_KEY=%s KITE_API_SECRET=%s KITE_ACCESS_TOKEN=%s KITE_USER_ID=%s KITE_DEFAULT_PRODUCT=%s KITE_DEFAULT_VARIETY=%s KITE_ORDER_VALIDITY=%s KITE_STOP_LOSS_MINIMUM_AMOUNT=%s KITE_STOP_LOSS_PERCENTAGE=%s KITE_REDIRECT_URL=%s KITE_AUTO_SAVE_TOKEN=%s",
            self.kite_api_key,
            self.kite_api_secret,
            self.kite_access_token,
            self.kite_user_id,
            self.kite_default_product,
            self.kite_default_variety,
            self.kite_order_validity,
            self.kite_stop_loss_minimum_amount,
            self.kite_stop_loss_percentage,
            self.kite_redirect_url,
            self.kite_auto_save_token,
        )


def get_settings() -> Settings:
    settings = Settings()
    settings.log_loaded_env()
    return settings
