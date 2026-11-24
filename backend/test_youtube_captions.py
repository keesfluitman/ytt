"""Caption track selection. yt-dlp is faked, so no network is needed."""

import asyncio
from pathlib import Path

import pytest

from app.services import youtube
from app.services.youtube import YouTubeTranscriptService

ERROR_429 = (
    "ERROR: Unable to download video subtitles for 'en': "
    "HTTP Error 429: Too Many Requests"
)


class FakeProcess:
    def __init__(self, returncode=0, stderr=""):
        self.returncode = returncode
        self._stderr = stderr

    async def communicate(self):
        await asyncio.sleep(0.01)
        return b"", self._stderr.encode()


def fake_yt_dlp(monkeypatch, tracks):
    """tracks: {track: caption text, or an Exception for a failing download}"""
    requested = []

    async def run(*cmd, **kwargs):
        track = cmd[cmd.index("--sub-lang") + 1]
        requested.append(track)
        content = tracks.get(track)
        if isinstance(content, Exception):
            return FakeProcess(1, f"WARNING: noise\n{content}\n")
        if content:
            out = Path(cmd[cmd.index("-o") + 1])
            out.with_name(f"{out.name}.{track}.vtt").write_text(
                f"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n{content}\n"
            )
        return FakeProcess()

    monkeypatch.setattr(youtube.asyncio, "create_subprocess_exec", run)
    return requested


@pytest.fixture
def service(monkeypatch, tmp_path):
    monkeypatch.setattr(youtube.settings, "TRANSCRIPT_DIR", tmp_path)
    service = YouTubeTranscriptService()
    monkeypatch.setattr(
        service.history_service, "get_youtube_transcript", lambda *a: None
    )
    monkeypatch.setattr(
        service.history_service, "add_transcript_entry", lambda **k: "entry"
    )

    async def subs(*a):
        return ["en"]

    monkeypatch.setattr(service, "check_available_subtitles", subs)
    return service


def fetch(service, monkeypatch, language="en", subtitle_langs=()):
    async def info(*a):
        return {
            "title": "t",
            "language": language,
            "subtitle_langs": list(subtitle_langs),
        }

    monkeypatch.setattr(service, "get_video_info", info)
    return asyncio.run(
        service.fetch_and_save_transcript(
            "https://www.youtube.com/watch?v=omCWNO7Jbnw"
        )
    )


def test_multi_audio_video_uses_the_original_track(service, monkeypatch):
    fake_yt_dlp(monkeypatch, {"en": Exception(ERROR_429), "en-orig": "We have talked"})
    result = fetch(service, monkeypatch)
    assert result["source_transcript_raw"] == "We have talked"
    assert result["source_lang"] == "en"


def test_manual_captions_win_over_the_original_auto_track(service, monkeypatch):
    fake_yt_dlp(monkeypatch, {"en": "manual", "en-orig": "auto"})
    result = fetch(service, monkeypatch, subtitle_langs=["en"])
    assert result["source_transcript_raw"] == "manual"


def test_plain_track_still_works_without_orig(service, monkeypatch):
    fake_yt_dlp(monkeypatch, {"en": "plain"})
    assert fetch(service, monkeypatch)["source_transcript_raw"] == "plain"


def test_native_language_fallback(service, monkeypatch):
    fake_yt_dlp(monkeypatch, {"en": Exception(ERROR_429), "fr-orig": "bonjour"})
    result = fetch(service, monkeypatch, language="fr")
    assert result["source_transcript_raw"] == "bonjour"
    assert result["source_lang"] == "fr"


def test_error_names_the_real_cause(service, monkeypatch):
    fake_yt_dlp(monkeypatch, {"en": Exception(ERROR_429)})
    with pytest.raises(ValueError, match="429"):
        fetch(service, monkeypatch)


def test_parallel_fetches_do_not_mix(service, monkeypatch):
    async def run(*cmd, **kwargs):
        out = Path(cmd[cmd.index("-o") + 1])
        out.with_name(f"{out.name}.en.vtt").write_text(f"WEBVTT\n\n{cmd[-1]}\n")
        return FakeProcess()

    monkeypatch.setattr(youtube.asyncio, "create_subprocess_exec", run)

    async def both():
        return await asyncio.gather(
            service.fetch_transcript("first", "en"),
            service.fetch_transcript("second", "en"),
        )

    texts = [text for text, _ in asyncio.run(both())]
    assert texts == ["first", "second"]
