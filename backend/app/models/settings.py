from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class ViewMode(str, Enum):
    SIDE_BY_SIDE = "side-by-side"
    PARAGRAPH = "paragraph"


class Theme(str, Enum):
    WHITE = "white"
    G10 = "g10"
    G80 = "g80"
    G90 = "g90"
    G100 = "g100"


class Settings(BaseModel):
    # Translation Settings
    default_target_language: str = Field(default="en", description="Default target language for translations")
    auto_translate: bool = Field(default=True, description="Automatically translate on fetch if languages differ")
    libretranslate_url: str = Field(default="http://libretranslate:5000", description="LibreTranslate server URL")
    
    # Display Settings  
    default_view_mode: ViewMode = Field(default=ViewMode.SIDE_BY_SIDE, description="Default view mode")
    font_size: Literal["small", "medium", "large"] = Field(default="medium", description="Font size for transcript display")
    theme: Theme = Field(default=Theme.WHITE, description="Carbon theme")
    highlight_color: str = Field(default="#0f62fe", description="Color for paragraph linking highlight")
    auto_paragraph_mobile: bool = Field(default=True, description="Auto-enable paragraph view on mobile")
    
    # Playback Settings (future)
    auto_scroll_speed: float = Field(default=1.0, ge=0.5, le=3.0, description="Auto-scroll speed multiplier")
    highlight_active: bool = Field(default=True, description="Highlight active paragraph during playback")
    default_playback_speed: float = Field(default=1.0, ge=0.25, le=2.0, description="Default playback speed")
    
    # Data Management
    history_retention_days: Optional[int] = Field(default=None, description="Days to keep history (None = unlimited)")
    
    # Advanced Settings
    api_timeout: int = Field(default=30, ge=10, le=120, description="API timeout in seconds")
    cache_duration_minutes: int = Field(default=60, ge=0, description="Cache duration for fetched transcripts")
    debug_mode: bool = Field(default=False, description="Enable debug mode")


class SettingsUpdate(BaseModel):
    # All fields optional for partial updates
    default_target_language: Optional[str] = None
    auto_translate: Optional[bool] = None
    libretranslate_url: Optional[str] = None
    
    default_view_mode: Optional[ViewMode] = None
    font_size: Optional[Literal["small", "medium", "large"]] = None
    theme: Optional[Theme] = None
    highlight_color: Optional[str] = None
    auto_paragraph_mobile: Optional[bool] = None
    
    auto_scroll_speed: Optional[float] = Field(None, ge=0.5, le=3.0)
    highlight_active: Optional[bool] = None
    default_playback_speed: Optional[float] = Field(None, ge=0.25, le=2.0)
    
    history_retention_days: Optional[int] = None
    
    api_timeout: Optional[int] = Field(None, ge=10, le=120)
    cache_duration_minutes: Optional[int] = Field(None, ge=0)
    debug_mode: Optional[bool] = None