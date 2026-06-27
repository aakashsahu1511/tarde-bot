import logging
from decimal import Decimal, ROUND_DOWN
from typing import Tuple

from fastapi import APIRouter

from app.config import settings

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




@router.post("/kite/webhook", tags=["kite"])
def kite_order_status_webhook() -> dict:
   return {"status": "ok", "message": "Kite WEBHOOK received successfully"}