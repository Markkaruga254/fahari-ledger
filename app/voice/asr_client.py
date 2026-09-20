"""
Sends a recorded call's audio URL to an external ASR provider and returns the
transcript. Two providers supported — pick one via ASR_PROVIDER in .env.

NOTE: Africa's Talking's Voice API records audio and hands you a URL via
callback; it does not transcribe. This module is the bridge to whichever
speech-to-text service you wire up. A failure here degrades gracefully
(returns None) rather than corrupting ledger data — the voice router falls
back to "please use USSD instead" when transcription fails.
"""
import base64
import logging

import requests

from app.config import settings

logger = logging.getLogger("fahari.voice.asr")

_DOWNLOAD_TIMEOUT = 10
_TRANSCRIBE_TIMEOUT = 30


def transcribe(recording_url: str) -> str | None:
    if settings.asr_provider == "whisper":
        return _transcribe_whisper(recording_url)
    if settings.asr_provider == "google":
        return _transcribe_google(recording_url)
    raise ValueError(f"Unknown ASR provider: {settings.asr_provider}")


def _transcribe_whisper(recording_url: str) -> str | None:
    try:
        audio = requests.get(recording_url, timeout=_DOWNLOAD_TIMEOUT).content
        resp = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.asr_api_key}"},
            files={"file": ("recording.wav", audio)},
            data={"model": "whisper-1", "language": "sw"},
            timeout=_TRANSCRIBE_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json().get("text")
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("whisper transcription failed: %s", exc)
        return None


def _google_encoding_for(recording_url: str) -> str:
    """Africa's Talking documents .wav and .mp3 as supported recording
    formats; Google's recognize API needs an explicit encoding for both
    (it can't sniff from the URL's bytes alone)."""
    lowered = recording_url.lower()
    if lowered.endswith(".mp3"):
        return "MP3"
    return "LINEAR16"


def _transcribe_google(recording_url: str) -> str | None:
    """Google Cloud Speech-to-Text v1 `speech:recognize`, sw-KE locale, per
    the controlled Kongowea item/price vocabulary this parser expects."""
    if not settings.asr_api_key:
        logger.warning("google transcription skipped: ASR_API_KEY is not set")
        return None

    try:
        audio_bytes = requests.get(recording_url, timeout=_DOWNLOAD_TIMEOUT).content
        resp = requests.post(
            "https://speech.googleapis.com/v1/speech:recognize",
            params={"key": settings.asr_api_key},
            json={
                "config": {
                    "encoding": _google_encoding_for(recording_url),
                    "languageCode": "sw-KE",
                    "alternativeLanguageCodes": ["en-KE"],
                    "enableAutomaticPunctuation": False,
                },
                "audio": {"content": base64.b64encode(audio_bytes).decode("ascii")},
            },
            timeout=_TRANSCRIBE_TIMEOUT,
        )
        resp.raise_for_status()
        results = resp.json().get("results", [])
        if not results:
            return None
        return results[0]["alternatives"][0]["transcript"]
    except Exception as exc:  # pragma: no cover - network dependent
        logger.warning("google transcription failed: %s", exc)
        return None
