import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.history import HistoryService
from app.services.translator import TranslationService
from app.services.llm import ClaudeRemoteService, LLMNotConfigured, LLMImproveError

logger = logging.getLogger(__name__)

router = APIRouter()
history_service = HistoryService()
translator = TranslationService()
llm = ClaudeRemoteService()


class ImproveRequest(BaseModel):
    entry_id: str


class ImproveResponse(BaseModel):
    entry_id: str
    improved_original: str
    improved_text: str
    summary: str
    provider: str
    paragraph_count: int
    processing_time: float


@router.get("/improve/status")
async def improve_status():
    """Whether remote-Claude improvement is configured and enabled."""
    return {"available": llm.available(), "model": settings.CLAUDE_MODEL}


@router.post("/improve", response_model=ImproveResponse)
async def improve_entry(req: ImproveRequest):
    start = time.time()

    entry = history_service.get_entry_by_id(req.entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    if not entry.original_text or not entry.original_text.strip():
        raise HTTPException(status_code=400, detail="Entry has no text to improve")

    source_lang = entry.source_lang or "auto"
    target_lang = entry.target_lang or settings.DEFAULT_TARGET_LANG

    # Split the raw transcript into rough paragraphs; Claude re-flows them into
    # logical paragraphs and aligns each with a natural translation.
    processed = translator.prepare_text_for_translation(entry.original_text)
    source_paragraphs = [p for p in processed.split("\n\n") if p.strip()]

    try:
        result = await llm.improve(source_paragraphs, source_lang, target_lang)
    except LLMNotConfigured as e:
        raise HTTPException(status_code=503, detail=str(e))
    except LLMImproveError as e:
        logger.error("Improve failed for %s: %s", req.entry_id, e)
        raise HTTPException(status_code=502, detail=f"Improvement failed: {e}")

    pairs = result["paragraphs"]
    improved_original = "\n\n".join(p["source"] for p in pairs)
    improved_text = "\n\n".join(p["target"] for p in pairs)
    provider = f"claude-{settings.CLAUDE_MODEL}"

    history_service.update_entry_improvement(
        req.entry_id,
        improved_original=improved_original,
        improved_text=improved_text,
        summary=result["summary"],
        provider=provider,
    )

    elapsed = time.time() - start
    logger.info(
        "Improved entry %s: %d paragraphs in %.1fs", req.entry_id, len(pairs), elapsed
    )

    return ImproveResponse(
        entry_id=req.entry_id,
        improved_original=improved_original,
        improved_text=improved_text,
        summary=result["summary"],
        provider=provider,
        paragraph_count=len(pairs),
        processing_time=elapsed,
    )
