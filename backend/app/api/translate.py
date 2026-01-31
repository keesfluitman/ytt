from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import time

from app.models.translation import (
    TranslationRequest,
    TranslationResponse,
    FileUploadResponse,
    LanguageDetectionResponse
)
from app.services.translator import TranslationService
from app.services.file_handler import FileHandler
from app.services.history import HistoryService
from app.config import settings

router = APIRouter()
translator = TranslationService()
file_handler = FileHandler()
history_service = HistoryService()


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    source_lang: str = Form("auto"),
    target_lang: str = Form("en"),
    provider: str = Form("libretranslate")
):
    start_time = time.time()
    
    if not text and not file:
        raise HTTPException(status_code=400, detail="Either text or file must be provided")
    
    if file:
        if file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit")
        
        text, file_format = await file_handler.extract_text(file)
    
    if len(text) > settings.MAX_TEXT_LENGTH:
        raise HTTPException(status_code=413, detail=f"Text length exceeds {settings.MAX_TEXT_LENGTH} characters")
    
    processed_text = translator.prepare_text_for_translation(text)
    
    try:
        result = await translator.translate(
            text=processed_text,
            source_lang=source_lang,
            target_lang=target_lang,
            provider=provider
        )
        
        processing_time = time.time() - start_time
        
        # Create response
        response = TranslationResponse(
            original_text=text,
            translated_text=result["translatedText"],
            source_lang=result.get("detectedLanguage", source_lang),
            target_lang=target_lang,
            provider=provider,
            processing_time=processing_time
        )
        
        # Save to history
        file_name = file.filename if file else None
        title = f"File: {file_name}" if file_name else None
        
        # Check if this text matches any YouTube transcript that we can update
        existing_youtube_entry = None
        if not file:  # Only check for YouTube match if this isn't a file translation
            history = history_service._load_history()
            for entry in history:
                if (entry.get("type") == "youtube" and 
                    entry.get("original_text") and
                    entry.get("source_lang") == result.get("detectedLanguage", source_lang) and
                    not entry.get("translated_text", "").strip()):  # No translation yet (check empty string too)
                    
                    # Check if the text matches (allowing for some text processing differences)
                    original_clean = entry.get("original_text", "").replace("\n", " ").replace("\r", "").strip()
                    text_clean = text.replace("\n", " ").replace("\r", "").strip()
                    
                    # If texts match closely, update the YouTube entry
                    if (original_clean == text_clean or 
                        len(set(original_clean.split()) & set(text_clean.split())) > len(text_clean.split()) * 0.8):
                        existing_youtube_entry = entry
                        break
        
        if existing_youtube_entry:
            # Update the existing YouTube entry with translation
            history_service.update_entry_translation(
                existing_youtube_entry["id"],
                result["translatedText"],
                target_lang,
                provider
            )
        else:
            # Create new translation entry
            history_service.add_translation_entry(
                original_text=text,
                translated_text=result["translatedText"],
                source_lang=result.get("detectedLanguage", source_lang),
                target_lang=target_lang,
                provider=provider,
                title=title
            )
        
        return response
    except Exception as e:
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
                alternatives=alternatives
            )
        else:
            raise HTTPException(status_code=500, detail="Invalid response from language detection")
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
            "url": settings.LIBRETRANSLATE_URL
        }
    ]
    
    if settings.OPENAI_API_KEY:
        providers.append({
            "id": "openai",
            "name": "OpenAI",
            "available": True
        })
    
    if settings.DEEPL_API_KEY:
        providers.append({
            "id": "deepl",
            "name": "DeepL",
            "available": True
        })
    
    return {"providers": providers}