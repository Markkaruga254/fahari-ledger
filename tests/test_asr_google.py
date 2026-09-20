from app.voice import asr_client


class _FakeResponse:
    def __init__(self, json_data, status_ok=True):
        self._json = json_data
        self._status_ok = status_ok

    def raise_for_status(self):
        if not self._status_ok:
            raise RuntimeError("http error")

    def json(self):
        return self._json

    @property
    def content(self):
        return b"fake-audio-bytes"


def test_google_transcription_returns_transcript(monkeypatch):
    monkeypatch.setattr(asr_client.settings, "asr_provider", "google")
    monkeypatch.setattr(asr_client.settings, "asr_api_key", "test-key")

    monkeypatch.setattr(
        asr_client.requests, "get", lambda url, timeout: _FakeResponse(None)
    )

    def fake_post(url, params, json, timeout):
        assert params == {"key": "test-key"}
        assert json["config"]["languageCode"] == "sw-KE"
        assert json["config"]["encoding"] == "LINEAR16"
        return _FakeResponse(
            {"results": [{"alternatives": [{"transcript": "kilo mbili za tilapia"}]}]}
        )

    monkeypatch.setattr(asr_client.requests, "post", fake_post)

    transcript = asr_client.transcribe("https://example.test/recording.wav")

    assert transcript == "kilo mbili za tilapia"


def test_google_transcription_uses_mp3_encoding_for_mp3_url(monkeypatch):
    monkeypatch.setattr(asr_client.settings, "asr_provider", "google")
    monkeypatch.setattr(asr_client.settings, "asr_api_key", "test-key")
    monkeypatch.setattr(asr_client.requests, "get", lambda url, timeout: _FakeResponse(None))

    seen = {}

    def fake_post(url, params, json, timeout):
        seen["encoding"] = json["config"]["encoding"]
        return _FakeResponse({"results": []})

    monkeypatch.setattr(asr_client.requests, "post", fake_post)

    asr_client.transcribe("https://example.test/recording.mp3")

    assert seen["encoding"] == "MP3"


def test_google_transcription_returns_none_without_results(monkeypatch):
    monkeypatch.setattr(asr_client.settings, "asr_provider", "google")
    monkeypatch.setattr(asr_client.settings, "asr_api_key", "test-key")
    monkeypatch.setattr(asr_client.requests, "get", lambda url, timeout: _FakeResponse(None))
    monkeypatch.setattr(
        asr_client.requests, "post", lambda *a, **k: _FakeResponse({"results": []})
    )

    assert asr_client.transcribe("https://example.test/recording.wav") is None


def test_google_transcription_skips_when_api_key_missing(monkeypatch):
    monkeypatch.setattr(asr_client.settings, "asr_provider", "google")
    monkeypatch.setattr(asr_client.settings, "asr_api_key", "")

    def unexpected_call(*args, **kwargs):
        raise AssertionError("should not call the network without an API key")

    monkeypatch.setattr(asr_client.requests, "get", unexpected_call)

    assert asr_client.transcribe("https://example.test/recording.wav") is None


def test_google_transcription_returns_none_on_http_error(monkeypatch):
    monkeypatch.setattr(asr_client.settings, "asr_provider", "google")
    monkeypatch.setattr(asr_client.settings, "asr_api_key", "test-key")
    monkeypatch.setattr(asr_client.requests, "get", lambda url, timeout: _FakeResponse(None))
    monkeypatch.setattr(
        asr_client.requests,
        "post",
        lambda *a, **k: _FakeResponse({}, status_ok=False),
    )

    assert asr_client.transcribe("https://example.test/recording.wav") is None
