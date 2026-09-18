from datetime import datetime

from scripts.seed_demo_data import _demo_event_timestamps


def test_demo_event_timestamps_stay_in_current_utc_day():
    now = datetime(2026, 9, 18, 3, 30, 0)

    purchase_at, sale_one_at, sale_two_at, debt_at = _demo_event_timestamps(now)

    assert purchase_at == datetime(2026, 9, 18, 8, 0, 0)
    assert sale_one_at == datetime(2026, 9, 18, 11, 0, 0)
    assert sale_two_at == datetime(2026, 9, 18, 13, 0, 0)
    assert debt_at == datetime(2026, 9, 18, 14, 0, 0)
