from pydantic import Field
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kite_api_key: str
    kite_api_secret: str
    kite_access_token: str
    kite_user_id: str

    kite_default_product: str = Field("MIS")
    kite_default_variety: str = Field("regular")
    kite_order_validity: str = Field("DAY")
    kite_stop_loss_minimum_amount: float = Field(10.0)
    kite_stop_loss_percentage: float = Field(0.10)

    model_config = ConfigDict(env_file='.env', env_file_encoding='utf-8')
