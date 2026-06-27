from pydantic import HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    kite_api_key: str
    kite_api_secret: str
    kite_redirect_url: HttpUrl
    kite_access_token: str | None = None
    kite_user_id: str | None = None
    kite_base_url: str = "https://api.kite.trade"
    kite_default_product: str = "MIS"
    kite_default_variety: str = "regular"
    kite_order_validity: str = "DAY"
    kite_auto_save_token: bool = False
    kite_stop_loss_minimum_amount: float = 10.0
    kite_stop_loss_percentage: float = 0.10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings: Settings = Settings()  # type: ignore[call-arg]
