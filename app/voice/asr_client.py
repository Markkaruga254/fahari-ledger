"""
Sends a recorded call's audio URL to an external ASR provider and returns the
transcript. Two providers stubbed — pick one via ASR_PROVIDER in .env.

NOTE: Africa's Talking's Voice API records audio and hands you a URL via
callback; it does not transcribe. This module is the bridge to whichever
speech-to-text service you wire up. Fill in the TODOs with real API calls
before the demo — these are intentionally left as network I/O only, so a
failure here degrades gracefully rather than corrupting ledger data.
"""
import requests

from app.config import settings


def transcribe(recording_url: str) -> str | None:
    if settings.asr_provider == "whisper":
        return _transcribe_whisper(recording_url)
    if settings.asr_provider == "google":
        return _transcribe_google(recording_url)
    raise ValueError(f"Unknown ASR provider: {settings.asr_provider}")


def _transcribe_whisper(recording_url: str) -> str | None:
    # TODO: download recording_url, POST to OpenAI's audio/transcriptions
    # endpoint with settings.asr_api_key, return the transcript text.
    try:
        audio = requests.get(recording_url, timeout=10).content
        resp = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.asr_api_key}"},
            files={"file": ("recording.wav", audio)},
            data={"model": "whisper-1", "language": "sw"},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("text")
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[asr] whisper transcription failed: {exc}")
        return None


def _transcribe_google(recording_url: str) -> str | None:
    # TODO: wire up Google Cloud Speech-to-Text with locale "sw-KE".
    raise NotImplementedError("Google STT path not implemented yet")
