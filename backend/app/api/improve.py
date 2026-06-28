import asyncio
import logging
import time
from typing import Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.history import HistoryService
from app.services.translator import TranslationService
from app.services.llm import ClaudeRemoteService, LLMImproveError

logger = logging.getLogger(__name__)

router = APIRouter()
history_service = HistoryService()
translator = TranslationService()
llm = ClaudeRemoteService()

# In-memory job registry: entry_id -> {status, ...}. Lost on restart, which is
# fine — the durable "done" signal is improved_text persisted on the entry.
# Improve runs as a background task so the HTTP request returns immediately and
# never hits a reverse-proxy timeout (Cloudflare cuts off at ~100s).
_jobs: Dict[str, dict] = {}
_tasks: Dict[str, asyncio.Task] = {}  # keep refs so tasks aren't garbage-collected


class ImproveRequest(BaseModel):
    entry_id: str
    force: bool = False  # skip the "already good?" pre-check and improve anyway


@router.get("/improve/status")
async def improve_status():
    """Whether remote-Claude improvement is configured/enabled (gates the UI)."""
    return {"available": llm.available(), "model": settings.CLAUDE_MODEL}


@router.get("/improve/state/{entry_id}")
async def improve_state(entry_id: str):
    """Current background-job state for an entry (polled by the frontend)."""
    return _jobs.get(entry_id, {"status": "idle"})


async def _run_improve(
    entry_id, source_paragraphs, source_lang, target_lang, translated_text, force
):
    start = time.time()
    try:
        # Cheap pre-check: don't burn a full improve on an already-good
        # translation unless the user explicitly forced it.
        if not force and translated_text and translated_text.strip():
            verdict = await llm.assess(translated_text, target_lang)
            if not verdict["needs_improvement"]:
                _jobs[entry_id] = {"status": "skipped", "reason": verdict["reason"]}
                logger.info("Skipped improve for %s (already good): %s",
                            entry_id, verdict["reason"])
                return

        result = await llm.improve(source_paragraphs, source_lang, target_lang)
        provider = f"claude-{settings.CLAUDE_MODEL}"
        history_service.update_entry_improvement(
            entry_id,
            improved_original="\n\n".join(result["segments"]),
            improved_text="\n\n".join(result["translations"]),
            summary=result["summary"],
            provider=provider,
        )
        elapsed = round(time.time() - start, 1)
        _jobs[entry_id] = {
            "status": "done",
            "paragraph_count": len(result["translations"]),
            "processing_time": elapsed,
            "provider": provider,
        }
        logger.info("Improved entry %s: %d paragraphs in %.1fs",
                    entry_id, len(result["translations"]), elapsed)
    except LLMImproveError as e:
        logger.error("Improve failed for %s: %s", entry_id, e)
        _jobs[entry_id] = {"status": "error", "message": str(e)}
    except Exception as e:  # noqa: BLE001 — surface any failure to the poller
        logger.exception("Unexpected improve error for %s", entry_id)
        _jobs[entry_id] = {"status": "error", "message": str(e)}
    finally:
        _tasks.pop(entry_id, None)


@router.post("/improve")
async def improve_entry(req: ImproveRequest):
    """Kick off a background improve job; returns immediately."""
    if not llm.available():
        raise HTTPException(status_code=503, detail="Improvement is not configured")

    entry = history_service.get_entry_by_id(req.entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if not entry.original_text or not entry.original_text.strip():
        raise HTTPException(status_code=400, detail="Entry has no text to improve")

    # Don't double-start a job that's already running for this entry.
    if _jobs.get(req.entry_id, {}).get("status") == "running":
        return {"status": "running"}

    source_lang = entry.source_lang or "auto"
    target_lang = entry.target_lang or settings.DEFAULT_TARGET_LANG
    processed = translator.prepare_text_for_translation(entry.original_text)
    source_paragraphs = [p for p in processed.split("\n\n") if p.strip()]
    if not source_paragraphs:
        raise HTTPException(status_code=400, detail="No paragraphs to improve")

    _jobs[req.entry_id] = {
        "status": "running",
        "paragraph_count": len(source_paragraphs),
    }
    task = asyncio.create_task(
        _run_improve(
            req.entry_id, source_paragraphs, source_lang, target_lang,
            entry.translated_text, req.force,
        )
    )
    _tasks[req.entry_id] = task

    logger.info("Started improve job for %s (%d paragraphs, force=%s)",
                req.entry_id, len(source_paragraphs), req.force)
    return {
        "status": "started",
        "entry_id": req.entry_id,
        "paragraph_count": len(source_paragraphs),
    }
