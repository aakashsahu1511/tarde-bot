from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, model_validator


class KiteOrderStatusPostback(BaseModel):
    order_id: str
    transaction_type: str
    tradingsymbol: str
    exchange: str
    product: str
    quantity: int
    status: Optional[str] = None
    order_status: Optional[str] = None
    average_price: Optional[float] = None
    price: Optional[float] = None
    filled_quantity: Optional[int] = None
    variety: Optional[str] = None
    instrument_type: Optional[str] = None
    order_timestamp: str
    checksum: str

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    @model_validator(mode="before")
    def normalize_status(cls, values):
        if values.get("order_status") is None and values.get("status") is not None:
            values["order_status"] = values["status"]
        return values

    @property
    def normalized_order_status(self) -> str:
        return (self.order_status or "").upper()

    @property
    def is_buy_order(self) -> bool:
        return self.transaction_type.upper() == "BUY"

    @property
    def executed_price(self) -> float:
        if self.average_price is not None and self.average_price > 0:
            return self.average_price
        if self.price is not None and self.price > 0:
            return self.price
        raise ValueError("Executed price is required in the Kite order payload")

    @property
    def is_final_status(self) -> bool:
        return self.normalized_order_status in {"COMPLETE", "CANCELLED"}
