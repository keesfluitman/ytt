import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from app.models.translation import TranslationHistory
from app.config import settings


class HistoryService:
    def __init__(self):
        self.history_file = settings.DATA_DIR / "history.json"
        self._ensure_history_file()
    
    def _ensure_history_file(self):
        """Ensure the history file exists with empty array"""
        if not self.history_file.exists():
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w') as f:
                json.dump([], f)
    
    def _load_history(self) -> List[Dict]:
        """Load all history entries"""
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def _save_history(self, history: List[Dict]):
        """Save history entries to file"""
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2, default=str, ensure_ascii=False)
    
    def add_translation_entry(
        self,
        original_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        provider: str,
        title: Optional[str] = None,
        video_id: Optional[str] = None,
        youtube_url: Optional[str] = None
    ) -> str:
        """Add a translation entry to history"""
        history = self._load_history()
        
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "title": title or self._generate_title(original_text),
            "original_text": original_text,
            "translated_text": translated_text,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "provider": provider,
            "created_at": datetime.now().isoformat(),
            "video_id": video_id,
            "youtube_url": youtube_url,
            "type": "youtube" if video_id else "text"
        }
        
        history.insert(0, entry)  # Add to beginning (newest first)
        self._save_history(history)
        
        return entry_id
    
    def add_transcript_entry(
        self,
        video_id: str,
        title: str,
        url: str,
        original_text: str,
        source_lang: str,
        available_languages: List[str],
        video_info: Dict,
        translated_text: Optional[str] = None,
        target_lang: Optional[str] = None,
        provider: Optional[str] = None
    ) -> str:
        """Add a YouTube transcript entry to history"""
        history = self._load_history()
        
        # Check if this video already exists
        existing_entry = self.find_youtube_entry(video_id, source_lang, target_lang)
        
        if existing_entry:
            # Update existing entry if we have new translation
            if translated_text and not existing_entry.get("translated_text"):
                return self.update_entry_translation(
                    existing_entry["id"],
                    translated_text,
                    target_lang or source_lang,
                    provider or "youtube"
                )
            return existing_entry["id"]
        
        # Create new entry
        entry_id = str(uuid.uuid4())
        entry = {
            "id": entry_id,
            "title": title,
            "original_text": original_text,
            "translated_text": translated_text or "",
            "source_lang": source_lang,
            "target_lang": target_lang or source_lang,  # Will be source_lang if no translation
            "provider": provider or "youtube",
            "created_at": datetime.now().isoformat(),
            "video_id": video_id,
            "youtube_url": url,
            "available_languages": available_languages,
            "video_info": video_info,
            "type": "youtube"
        }
        
        history.insert(0, entry)
        self._save_history(history)
        
        return entry_id
    
    def update_entry_translation(
        self,
        entry_id: str,
        translated_text: str,
        target_lang: str,
        provider: str
    ) -> str:
        """Update an existing entry with translation"""
        history = self._load_history()
        
        for entry in history:
            if entry.get("id") == entry_id:
                entry["translated_text"] = translated_text
                entry["target_lang"] = target_lang
                entry["provider"] = provider
                entry["updated_at"] = datetime.now().isoformat()
                break
        
        self._save_history(history)
        return entry_id
    
    def find_youtube_entry(
        self,
        video_id: str,
        source_lang: str,
        target_lang: Optional[str] = None
    ) -> Optional[Dict]:
        """Find existing YouTube entry by video ID and languages"""
        history = self._load_history()
        
        for entry in history:
            if (entry.get("video_id") == video_id and 
                entry.get("source_lang") == source_lang and
                entry.get("type") == "youtube"):
                # If target_lang specified, it should match
                if target_lang and entry.get("target_lang") != target_lang:
                    continue
                return entry
        
        return None
    
    def get_youtube_transcript(
        self,
        video_id: str,
        source_lang: str,
        target_lang: Optional[str] = None
    ) -> Optional[Dict]:
        """Get cached YouTube transcript data"""
        entry = self.find_youtube_entry(video_id, source_lang, target_lang)
        
        if entry:
            return {
                "title": entry.get("title", ""),
                "original_text": entry.get("original_text", ""),
                "translated_text": entry.get("translated_text", ""),
                "source_lang": entry.get("source_lang", source_lang),
                "target_lang": entry.get("target_lang", target_lang or source_lang),
                "available_languages": entry.get("available_languages", []),
                "video_info": entry.get("video_info", {}),
                "cached": True,
                "entry_id": entry.get("id")
            }
        
        return None
    
    def get_all_entries(
        self,
        limit: int = 20,
        offset: int = 0,
        source_lang: Optional[str] = None,
        target_lang: Optional[str] = None
    ) -> List[TranslationHistory]:
        """Get all history entries with optional filtering"""
        history = self._load_history()
        
        # Filter by language if specified
        if source_lang:
            history = [h for h in history if h.get("source_lang") == source_lang]
        if target_lang:
            history = [h for h in history if h.get("target_lang") == target_lang]
        
        # Apply pagination
        paginated = history[offset:offset + limit]
        
        # Convert to TranslationHistory objects
        return [TranslationHistory(**item) for item in paginated]
    
    def get_entry_by_id(self, entry_id: str) -> Optional[TranslationHistory]:
        """Get a specific entry by ID"""
        history = self._load_history()
        
        for item in history:
            if item.get("id") == entry_id:
                return TranslationHistory(**item)
        
        return None
    
    def delete_entry(self, entry_id: str) -> bool:
        """Delete an entry by ID"""
        history = self._load_history()
        original_length = len(history)
        
        history = [h for h in history if h.get("id") != entry_id]
        
        if len(history) < original_length:
            self._save_history(history)
            return True
        
        return False
    
    def clear_all(self):
        """Clear all history entries"""
        self._save_history([])
    
    def _generate_title(self, text: str, max_length: int = 50) -> str:
        """Generate a title from text content"""
        if not text:
            return "Untitled"
        
        # Take first sentence or first 50 chars
        first_sentence = text.split('.')[0].strip()
        if len(first_sentence) <= max_length:
            return first_sentence
        
        return text[:max_length].strip() + "..."