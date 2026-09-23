import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.utils.logging import setup_logging

setup_logging()

from app.ussd.router import router as ussd_router
from app.voice.router import router as voice_router
from app.sms.router import router as sms_router
from app.sms.scheduler import start_scheduler
from app.db.session import Base, SessionLocal, engine

logger = logging.getLogger("fahari.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Idempotent: a fresh `docker compose up` serves USSD immediately even
    # before the demo seed has ever run. (Alembic migrations can replace this
    # post-hackathon; see app/db/migrations/README.md.)
    Base.metadata.create_all(engine)
    start_scheduler()
    logger.info("Fahari Ledger started")
    yield


app = FastAPI(title="Fahari Ledger", lifespan=lifespan)

app.include_router(ussd_router)
app.include_router(voice_router)
app.include_router(sms_router)


@app.get("/health")
def health():
    """Liveness: the process is up. Does not touch the database."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness: the database is actually reachable.

    Use this (not /health) for deploy-time and pre-demo checks — a container
    that answers /health but not /ready has started but can't yet serve a
    real USSD/Voice transaction.
    """
    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
        finally:
            db.close()
        return {"status": "ready"}
    except Exception as exc:
        logger.error("readiness check failed: %s", exc)
        return JSONResponse(status_code=503, content={"status": "not ready", "error": str(exc)})
