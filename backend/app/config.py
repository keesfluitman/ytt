from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path


class Settings(BaseSettings):
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    APP_DEBUG: bool = False
    
    LIBRETRANSLATE_URL: str = "http://localhost:5000"
    LIBRETRANSLATE_API_KEY: str = ""
    
    OPENAI_API_KEY: str = ""
    DEEPL_API_KEY: str = ""
    
    DATABASE_URL: str = "sqlite:///./ytt.db"
    
    REDIS_URL: str = ""
    CACHE_TTL: int = 3600
    
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    MAX_FILE_SIZE_MB: int = 10
    RATE_LIMIT: str = "100/minute"
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",  # Development frontend
        "http://localhost:8000",  # Production same-origin
        "http://localhost:8090",  # Alternative dev port
        "https://localhost:8000", # HTTPS variant
        "*"  # Allow all origins in production (since we're serving static files)
    ]
    
    SUPPORTED_FORMATS: List[str] = ["txt", "srt", "vtt", "md", "docx", "pdf", "json", "yaml"]
    
    DEFAULT_SOURCE_LANG: str = "auto"
    DEFAULT_TARGET_LANG: str = "de"
    CHUNK_SIZE: int = 5000
    MAX_TEXT_LENGTH: int = 50000
    
    DATA_DIR: Path = Path("./data")
    UPLOAD_DIR: Path = Path("./data/uploads")
    TRANSCRIPT_DIR: Path = Path("./data/transcripts")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.DATA_DIR.mkdir(exist_ok=True)
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.TRANSCRIPT_DIR.mkdir(exist_ok=True)


settings = Settings()