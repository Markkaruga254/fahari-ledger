"""
Deliberately NOT a trained model. A simple, explainable threshold rule:
if it's past OVERSTOCK_HOUR_THRESHOLD and more than OVERSTOCK_STOCK_RATIO of
what was bought this morning is still unsold, nudge the vendor to discount.
"""
from datetime import datetime

from app.config import settings


def should_nudge(purchased_qty: float, sold_qty: float, now: datetime = None) -> bool:
    now = now or datetime.utcnow()
    if purchased_qty <= 0:
        return False
    remaining_ratio = max(purchased_qty - sold_qty, 0) / purchased_qty
    return now.hour >= settings.overstock_hour_threshold and remaining_ratio > settings.overstock_stock_ratio


def nudge_message(item: str, remaining_qty: float, unit: str = "kg") -> str:
    return (
        f"You have {remaining_qty:.1f}{unit} {item} left and it's late in the day. "
        f"Discount now or risk a loss tomorrow."
    )
