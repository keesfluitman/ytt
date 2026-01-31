from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.models.translation import TranslationHistory
from app.services.history import HistoryService
from app.config import settings

router = APIRouter()
history_service = HistoryService()


@router.get("/history", response_model=List[TranslationHistory])
async def get_translation_history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None
):
    return history_service.get_all_entries(limit, offset, source_lang, target_lang)


@router.get("/history/{translation_id}", response_model=TranslationHistory)
async def get_translation_by_id(translation_id: str):
    entry = history_service.get_entry_by_id(translation_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Translation not found")
    return entry


@router.delete("/history/{translation_id}")
async def delete_translation(translation_id: str):
    success = history_service.delete_entry(translation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Translation not found")
    return {"message": "Translation deleted successfully"}


@router.delete("/history")
async def clear_history():
    history_service.clear_all()
    return {"message": "History cleared successfully"}