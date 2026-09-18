from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Sale, Vendor
from app.db.session import Base
from app.services import notifications
from app.voice import router
from app.voice.item_parser import parse_transcript


PHONE = "+254700000011"


def _body(response):
    return response.body.decode("utf-8")


def test_parse_swahili_sale_transcript():
    parsed = parse_transcript("kilo mbili za tilapia, bei mia tatu")
    assert parsed == {"item": "tilapia", "quantity": 2.0, "price": 300.0}


def test_parse_digit_sale_transcript():
    parsed = parse_transcript("I sold 5kg tilapia for 3000")
    assert parsed == {"item": "tilapia", "quantity": 5.0, "price": 3000.0}


def test_parse_requires_known_item_and_quantity():
    assert parse_transcript("I sold something for 3000") is None
    assert parse_transcript("tilapia for 3000") is None


def test_voice_callback_uses_public_recording_url(monkeypatch):
    monkeypatch.setattr(router.settings, "public_base_url", "https://demo.example.com")

    response = __import__("asyncio").run(router.voice_callback(PHONE))
    body = _body(response)

    assert response.media_type == "application/xml"
    assert 'callbackUrl="https://demo.example.com/voice/recording"' in body


def test_voice_callback_falls_back_to_relative_url(monkeypatch):
    monkeypatch.setattr(router.settings, "public_base_url", "")

    response = __import__("asyncio").run(router.voice_callback(PHONE))
    body = _body(response)

    assert response.media_type == "application/xml"
    assert 'callbackUrl="/voice/recording"' in body


def test_voice_recording_persists_sale_and_sends_sms(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    router.SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(router, "transcribe", lambda url: "I sold 5kg tilapia for 3000")

    sent = []
    monkeypatch.setattr(
        notifications,
        "send_voice_sale_confirmation",
        lambda to, item, quantity, price: sent.append((to, item, quantity, price)),
    )

    try:
        response = __import__("asyncio").run(
            router.voice_recording_callback(PHONE, "https://example.test/recording.wav")
        )

        body = _body(response)
        assert response.media_type == "application/xml"
        assert "Confirmed: sold 5 tilapia for 3000 shillings" in body
        assert sent == [(PHONE, "tilapia", 5.0, 3000.0)]

        db = router.SessionLocal()
        try:
            sale = db.query(Sale).one()
            vendor = db.query(Vendor).filter_by(phone_number=PHONE).one()
            assert sale.vendor_id == vendor.id
            assert sale.item == "tilapia"
            assert sale.quantity == 5
            assert sale.price == 3000
            assert sale.source == "voice"
        finally:
            db.close()
    finally:
        router.SessionLocal = None
        engine.dispose()


def test_voice_recording_rejects_incomplete_transcript(monkeypatch):
    monkeypatch.setattr(router, "transcribe", lambda url: "I sold 5kg tilapia")

    response = __import__("asyncio").run(
        router.voice_recording_callback(PHONE, "https://example.test/recording.wav")
    )

    assert "did not catch the full details" in _body(response)
