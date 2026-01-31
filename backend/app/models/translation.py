from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TranslationProvider(str, Enum):
    LIBRETRANSLATE = "libretranslate"
    OPENAI = "openai"
    DEEPL = "deepl"


class TranslationRequest(BaseModel):
    text: Optional[str] = None
    source_lang: str = "auto"
    target_lang: str = "en"
    provider: TranslationProvider = TranslationProvider.LIBRETRANSLATE
    preserve_formatting: bool = True
    context: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Bonjour le monde",
                "source_lang": "fr",
                "target_lang": "en",
                "provider": "libretranslate"
            }
        }


class TranslationResponse(BaseModel):
    id: Optional[str] = None
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    provider: str
    confidence: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)
    processing_time: Optional[float] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "trans_123",
                "original_text": "Bonjour le monde",
                "translated_text": "Hello world",
                "source_lang": "fr",
                "target_lang": "en",
                "provider": "libretranslate",
                "confidence": 0.95,
                "created_at": "2024-01-27T10:00:00",
                "processing_time": 0.5
            }
        }


class FileUploadResponse(BaseModel):
    filename: str
    content_type: str
    size: int
    text_content: str
    detected_format: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "transcript.txt",
                "content_type": "text/plain",
                "size": 1024,
                "text_content": "This is the extracted text...",
                "detected_format": "txt"
            }
        }


class LanguageDetectionResponse(BaseModel):
    detected_language: str
    confidence: float
    alternatives: Optional[List[dict]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "detected_language": "fr",
                "confidence": 0.98,
                "alternatives": [
                    {"language": "es", "confidence": 0.15},
                    {"language": "it", "confidence": 0.10}
                ]
            }
        }


class TranslationHistory(BaseModel):
    id: str
    title: Optional[str] = None
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    provider: str
    created_at: datetime
    file_name: Optional[str] = None
    file_type: Optional[str] = None
    video_id: Optional[str] = None
    youtube_url: Optional[str] = None
    available_languages: Optional[List[str]] = None
    video_info: Optional[dict] = None
    type: Optional[str] = None  # "text", "youtube", "file"
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True