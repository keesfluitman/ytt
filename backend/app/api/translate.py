import logging
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import time

from app.models.translation import (
    TranslationRequest,
    TranslationResponse,
    FileUploadResponse,
    LanguageDetectionResponse,
)
from app.services.translator import TranslationService
from app.services.file_handler import FileHandler
from app.services.history import HistoryService
from app.services.youtube import YouTubeTranscriptService
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
translator = TranslationService()
file_handler = FileHandler()
history_service = HistoryService()
youtube_service = YouTubeTranscriptService()


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    source_lang: str = Form("auto"),
    target_lang: str = Form("en"),
    provider: str = Form("libretranslate"),
    entry_id: Optional[str] = Form(None),
):
    start_time = time.time()

    if not text and not file:
        raise HTTPException(
            status_code=400, detail="Either text or file must be provided"
        )

    if file:
        if file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
            )

        text, file_format = await file_handler.extract_text(file)

    if len(text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=413,
            detail=f"Text length exceeds {settings.MAX_TEXT_LENGTH} characters",
        )

    logger.info(
        "Translate request: %d chars, %s -> %s, entry_id=%s",
        len(text),
        source_lang,
        target_lang,
        entry_id,
    )

    processed_text = translator.prepare_text_for_translation(text)

    try:
        result = await translator.translate(
            text=processed_text,
            source_lang=source_lang,
            target_lang=target_lang,
            provider=provider,
        )

        processing_time = time.time() - start_time

        # Create response
        response = TranslationResponse(
            original_text=text,
            translated_text=result["translatedText"],
            source_lang=result.get("detectedLanguage", source_lang),
            target_lang=target_lang,
            provider=provider,
            processing_time=processing_time,
        )

        # Save to history
        if entry_id:
            # Update existing entry (e.g., YouTube transcript being translated)
            logger.info("Updating existing entry %s with translation", entry_id)
            history_service.update_entry_translation(
                entry_id, result["translatedText"], target_lang, provider
            )
            # Also save translation file to the entry's folder
            existing_entry = history_service.get_entry_by_id(entry_id)
            if existing_entry and existing_entry.video_id:
                youtube_service.save_translation_to_folder(
                    existing_entry.video_id, target_lang, result["translatedText"]
                )
        else:
            # Create new translation entry (standalone text/file translation)
            file_name = file.filename if file else None
            title = f"File: {file_name}" if file_name else None
            logger.info("Creating new translation entry (title=%s)", title)
            history_service.add_translation_entry(
                original_text=text,
                translated_text=result["translatedText"],
                source_lang=result.get("detectedLanguage", source_lang),
                target_lang=target_lang,
                provider=provider,
                title=title,
            )

        return response
    except Exception as e:
        logger.error("Translation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/translate/detect", response_model=LanguageDetectionResponse)
async def detect_language(text: str = Form(...)):
    try:
        result = await translator.detect_language(text)

        if isinstance(result, list) and len(result) > 0:
            detected = result[0]
            alternatives = result[1:] if len(result) > 1 else None

            return LanguageDetectionResponse(
                detected_language=detected["language"],
                confidence=detected["confidence"],
                alternatives=alternatives,
            )
        else:
            raise HTTPException(
                status_code=500, detail="Invalid response from language detection"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages")
async def get_supported_languages():
    try:
        languages = await translator.get_supported_languages()
        return {"languages": languages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def get_translation_providers():
    providers = [
        {
            "id": "libretranslate",
            "name": "LibreTranslate",
            "available": True,
            "url": settings.LIBRETRANSLATE_URL,
        }
    ]

    if settings.OPENAI_API_KEY:
        providers.append({"id": "openai", "name": "OpenAI", "available": True})

    if settings.DEEPL_API_KEY:
        providers.append({"id": "deepl", "name": "DeepL", "available": True})

    return {"providers": providers}
