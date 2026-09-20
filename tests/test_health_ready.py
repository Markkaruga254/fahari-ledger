from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main


def test_health_is_always_ok():
    assert main.health() == {"status": "ok"}


def test_ready_returns_ready_when_db_is_reachable(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    monkeypatch.setattr(
        main, "SessionLocal", sessionmaker(bind=engine, autoflush=False, autocommit=False)
    )

    result = main.ready()

    assert result == {"status": "ready"}
    engine.dispose()


def test_ready_returns_503_when_db_is_unreachable(monkeypatch):
    class BrokenSession:
        def execute(self, *args, **kwargs):
            raise ConnectionError("db unreachable")

        def close(self):
            pass

    monkeypatch.setattr(main, "SessionLocal", lambda: BrokenSession())

    response = main.ready()

    assert response.status_code == 503
    body = response.body.decode("utf-8")
    assert "not ready" in body
    assert "db unreachable" in body
