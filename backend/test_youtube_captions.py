"""Caption download. yt-dlp is faked, so no network is needed."""

import asyncio
from pathlib import Path

import pytest

from app.services import youtube
from app.services.youtube import YouTubeTranscriptService

class FakeProcess:
    def __init__(self, returncode=0, stderr=""):
        self.returncode = returncode
        self._stderr = stderr

    async def communicate(self):
        await asyncio.sleep(0.01)
        return b"", self._stderr.encode()


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

    texts = asyncio.run(both())
    assert texts == ["first", "second"]
