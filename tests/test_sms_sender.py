from app.sms import sender


def test_send_sms_retries_and_succeeds(monkeypatch):
    monkeypatch.setattr(sender, "_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(sender.time, "sleep", lambda *_: None)

    calls = []

    def flaky_send(message, recipients, sender_id):
        calls.append((message, recipients, sender_id))
        if len(calls) < 2:
            raise ConnectionError("network blip")
        return {"ok": True}

    monkeypatch.setattr(sender.at_sms, "send", flaky_send)

    result = sender.send_sms("+254700000000", "hello")

    assert result == {"ok": True}
    assert len(calls) == 2  # failed once, succeeded on retry


def test_send_sms_returns_error_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr(sender, "_BACKOFF_SECONDS", 0)
    monkeypatch.setattr(sender.time, "sleep", lambda *_: None)

    attempts = []

    def always_fails(message, recipients, sender_id):
        attempts.append(1)
        raise ConnectionError("network down")

    monkeypatch.setattr(sender.at_sms, "send", always_fails)

    result = sender.send_sms("+254700000000", "hello")

    assert len(attempts) == sender._MAX_ATTEMPTS
    assert "network down" in result["error"]


def test_send_sms_succeeds_first_try_without_retrying(monkeypatch):
    calls = []
    monkeypatch.setattr(
        sender.at_sms,
        "send",
        lambda message, recipients, sender_id: calls.append(1) or {"ok": True},
    )

    result = sender.send_sms("+254700000000", "hello")

    assert result == {"ok": True}
    assert len(calls) == 1
