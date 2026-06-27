import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


class Settings:
    kite_api_key: str = ""
    kite_api_secret: str = ""
    kite_access_token: str | None = None
    kite_user_id: str | None = None

    kite_default_product: str = "MIS"
    kite_default_variety: str = "regular"
    kite_order_validity: str = "DAY"
    kite_stop_loss_minimum_amount: float = 10.0
    kite_stop_loss_percentage: float = 0.10
    kite_redirect_url: str | None = None
    kite_auto_save_token: bool = False

    def __init__(self, **values: Any) -> None:
        for name, value in values.items():
            setattr(self, name, value)

    def log_loaded_env(self) -> None:
        logger.info(
            "Loaded Kite settings from code: KITE_API_KEY=%s KITE_API_SECRET=%s KITE_ACCESS_TOKEN=%s KITE_USER_ID=%s KITE_DEFAULT_PRODUCT=%s KITE_DEFAULT_VARIETY=%s KITE_ORDER_VALIDITY=%s KITE_STOP_LOSS_MINIMUM_AMOUNT=%s KITE_STOP_LOSS_PERCENTAGE=%s KITE_REDIRECT_URL=%s KITE_AUTO_SAVE_TOKEN=%s",
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
    # Allow environment variables to override hard-coded defaults. This keeps
    # the convenience of in-file defaults while allowing tests or runtime
    # env vars to take precedence.
    def _parse_bool(val: str | None) -> bool:
        return str(val).lower() in ("1", "true", "yes", "on") if val is not None else False

    values: dict[str, Any] = {}
    if os.getenv("KITE_API_KEY"):
        values["kite_api_key"] = os.getenv("KITE_API_KEY")
    if os.getenv("KITE_API_SECRET"):
        values["kite_api_secret"] = os.getenv("KITE_API_SECRET")
    if os.getenv("KITE_ACCESS_TOKEN"):
        values["kite_access_token"] = os.getenv("KITE_ACCESS_TOKEN")
    if os.getenv("KITE_USER_ID"):
        values["kite_user_id"] = os.getenv("KITE_USER_ID")
    if os.getenv("KITE_DEFAULT_PRODUCT"):
        values["kite_default_product"] = os.getenv("KITE_DEFAULT_PRODUCT")
    if os.getenv("KITE_DEFAULT_VARIETY"):
        values["kite_default_variety"] = os.getenv("KITE_DEFAULT_VARIETY")
    if os.getenv("KITE_ORDER_VALIDITY"):
        values["kite_order_validity"] = os.getenv("KITE_ORDER_VALIDITY")
    if os.getenv("KITE_STOP_LOSS_MINIMUM_AMOUNT"):
        try:
            values["kite_stop_loss_minimum_amount"] = float(os.getenv("KITE_STOP_LOSS_MINIMUM_AMOUNT"))
        except (TypeError, ValueError):
            pass
    if os.getenv("KITE_STOP_LOSS_PERCENTAGE"):
        try:
            values["kite_stop_loss_percentage"] = float(os.getenv("KITE_STOP_LOSS_PERCENTAGE"))
        except (TypeError, ValueError):
            pass
    if os.getenv("KITE_REDIRECT_URL"):
        values["kite_redirect_url"] = os.getenv("KITE_REDIRECT_URL")
    if os.getenv("KITE_AUTO_SAVE_TOKEN"):
        values["kite_auto_save_token"] = _parse_bool(os.getenv("KITE_AUTO_SAVE_TOKEN"))

    settings = Settings(**values) if values else Settings()
    settings.log_loaded_env()
    return settings
