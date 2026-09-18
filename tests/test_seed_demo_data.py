from datetime import datetime

from scripts.seed_demo_data import _demo_event_times


def test_demo_event_times_stay_within_current_business_day():
    now = datetime(2026, 9, 18, 1, 15)
    event_times = _demo_event_times(now)

    assert event_times["purchase"] == datetime(2026, 9, 18, 8, 0)
    assert event_times["sale_one"] == datetime(2026, 9, 18, 11, 0)
    assert event_times["sale_two"] == datetime(2026, 9, 18, 13, 0)
    assert event_times["debt"] == datetime(2026, 9, 18, 14, 0)
