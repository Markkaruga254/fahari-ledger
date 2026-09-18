from app.services import notifications


def test_debt_notification_uses_sms_adapter(monkeypatch):
    sent = []

    monkeypatch.setattr(
        notifications,
        "send_sms",
        lambda to, message: sent.append((to, message)) or {"ok": True},
    )

    result = notifications.send_debt_reminder(
        "+254711111111",
        2000,
        "tilapia",
        "Kongowea Fish Seller",
    )

    assert result == {"ok": True}
    assert sent == [(
        "+254711111111",
        "You owe Kongowea Fish Seller KES 2000 for tilapia, logged today via Fahari Ledger.",
    )]


def test_notification_delivery_failure_stays_at_adapter_boundary(monkeypatch):
    monkeypatch.setattr(
        notifications,
        "send_sms",
        lambda to, message: {"error": "network unavailable"},
    )

    result = notifications.send_overstock_alert("+254700000000", "tilapia", 17)

    assert result == {"error": "network unavailable"}
