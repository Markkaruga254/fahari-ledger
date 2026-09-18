from datetime import datetime

from app.services import overstock


def test_nudges_when_late_and_overstocked():
    now = datetime(2026, 9, 18, 16, 0)  # 4pm, past the default 3pm threshold
    assert overstock.should_nudge(purchased_qty=15, sold_qty=3, now=now) is True


def test_no_nudge_when_mostly_sold():
    now = datetime(2026, 9, 18, 16, 0)
    assert overstock.should_nudge(purchased_qty=15, sold_qty=13, now=now) is False


def test_no_nudge_before_threshold_hour():
    now = datetime(2026, 9, 18, 10, 0)
    assert overstock.should_nudge(purchased_qty=15, sold_qty=1, now=now) is False
