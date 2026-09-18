from fastapi import FastAPI

from app.ussd.router import router as ussd_router
from app.voice.router import router as voice_router
from app.sms.scheduler import start_scheduler

app = FastAPI(title="Fahari Ledger")

app.include_router(ussd_router)
app.include_router(voice_router)


@app.on_event("startup")
def on_startup():
    start_scheduler()


@app.get("/health")
def health():
    return {"status": "ok"}
