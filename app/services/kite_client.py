import logging

from app.config import Settings
from app.models.schemas import KiteOrderStatusPostback

logger = logging.getLogger(__name__)


class KiteClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        if not self.settings.kite_access_token:
            raise ValueError("Kite access token is not configured. Authenticate via /kite/auth/login first.")

        from kiteconnect import KiteConnect

        self.client = KiteConnect(
            api_key=self.settings.kite_api_key,
            access_token=self.settings.kite_access_token,
        )

    def place_sell_stop_loss(
        self,
        order: KiteOrderStatusPostback,
        trigger_price: float,
        limit_price: float,
    ) -> dict:
        from kiteconnect import KiteException

        payload = {
            "tradingsymbol": order.tradingsymbol,
            "exchange": order.exchange,
            "transaction_type": "SELL",
            "quantity": order.quantity,
            "order_type": "SL",
            "product": order.product or self.settings.kite_default_product,
            "variety": order.variety or self.settings.kite_default_variety,
            "price": limit_price,
            "trigger_price": trigger_price,
            "validity": self.settings.kite_order_validity,
            "tag": "stop_loss",
        }
        logger.info("Placing Kite stop-loss order for completed buy order %s", order.order_id)
        try:
            return self.client.place_order(**payload)
        except KiteException as exc:
            logger.exception("Kite order placement failed for order_id=%s", order.order_id)
            raise
