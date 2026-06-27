import hashlib
import logging
from decimal import Decimal, ROUND_DOWN
from typing import Tuple

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status

from app.config import Settings
from app.models.schemas import KiteOrderStatusPostback, KiteWebhookEvent
from app.services.kite_client import KiteClient

router = APIRouter()
logger = logging.getLogger(__name__)


def calculate_stop_loss_levels(
    executed_price: float,
    minimum_amount: float,
    percentage: float,
) -> Tuple[float, float]:
    distance = max(executed_price * percentage, minimum_amount)
    trigger_price = float(Decimal(executed_price - distance).quantize(Decimal("0.01"), rounding=ROUND_DOWN))
    if trigger_price <= 0:
        raise ValueError("Computed stop-loss trigger price must be greater than zero")

    limit_price = float(Decimal(trigger_price - 0.05).quantize(Decimal("0.01"), rounding=ROUND_DOWN))
    if limit_price <= 0:
        limit_price = trigger_price
    return trigger_price, limit_price


def verify_kite_checksum(payload: KiteOrderStatusPostback, secret: str) -> bool:
    checksum_seed = f"{payload.order_id}{payload.order_timestamp}{secret}"
    expected = hashlib.sha256(checksum_seed.encode("utf-8")).hexdigest()
    return expected == payload.checksum


@router.post("/sample", tags=["sample"])
def kite_order_status_webhook(event: KiteWebhookEvent) -> dict:
    payload = event.order_payload()
    logger.info("Received Kite sample webhook event=%s order_id=%s", event.type or event.event, payload.order_id)
    settings = Settings()  # type: ignore[call-arg]

    if not verify_kite_checksum(payload, settings.kite_api_secret):
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="Invalid checksum",
        )

    return {
        "status": "received",
        "event_type": event.type or event.event,
        "order_id": payload.order_id,
        "order_status": payload.order_status,
        "transaction_type": payload.transaction_type,
    }

    # if not verify_kite_checksum(payload, settings.kite_api_secret):
    #     raise HTTPException(
    #         status_code=http_status.HTTP_400_BAD_REQUEST,
    #         detail="Invalid checksum",
    #     )

    # if not payload.is_final_status:
    #     return {
    #         "status": "ignored",
    #         "reason": "order status is not COMPLETE or CANCELLED",
    #         "order_status": payload.order_status,
    #     }

    # if not payload.is_buy_order:
    #     return {
    #         "status": "ignored",
    #         "reason": "only completed BUY orders trigger stop-loss creation",
    #         "transaction_type": payload.transaction_type,
    #     }

    # try:
    #     executed_price = payload.executed_price
    #     trigger_price, limit_price = calculate_stop_loss_levels(
    #         executed_price,
    #         settings.kite_stop_loss_minimum_amount,
    #         settings.kite_stop_loss_percentage,
    #     )
    # except ValueError as exc:
    #     raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # kite_client = KiteClient(settings)

    # try:
    #     kite_response = kite_client.place_sell_stop_loss(payload, trigger_price, limit_price)
    # except Exception as exc:
    #     logger.exception("Failed to place sell stop-loss order for order_id=%s", payload.order_id)
    #     raise HTTPException(
    #         status_code=http_status.HTTP_502_BAD_GATEWAY,
    #         detail="Failed to place sell stop-loss order",
    #     ) from exc

    # return {
    #     "status": "created",
    #     "message": "Sell stop-loss order created",
    #     "original_order_id": payload.order_id,
    #     "trigger_price": trigger_price,
    #     "limit_price": limit_price,
    #     "kite_response": kite_response,
    # }
