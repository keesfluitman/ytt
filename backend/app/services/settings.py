import json
from pathlib import Path
from typing import Optional

from app.models.settings import Settings, SettingsUpdate


class SettingsService:
    def __init__(self, settings_file: Optional[Path] = None):
        self.settings_file = settings_file or Path("data/settings.json")
        self.settings_file.parent.mkdir(parents=True, exist_ok=True)
        self._settings: Optional[Settings] = None
        self._load_settings()
    
    def _load_settings(self) -> Settings:
        """Load settings from file or create defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    data = json.load(f)
                    self._settings = Settings(**data)
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error loading settings: {e}. Using defaults.")
                self._settings = Settings()
                self._save_settings()
        else:
            self._settings = Settings()
            self._save_settings()
        
        return self._settings
    
    def _save_settings(self) -> None:
        """Save current settings to file"""
        with open(self.settings_file, 'w') as f:
            json.dump(self._settings.model_dump(), f, indent=2)
    
    def get_settings(self) -> Settings:
        """Get current settings"""
        if self._settings is None:
            self._load_settings()
        return self._settings
    
    def update_settings(self, updates: SettingsUpdate) -> Settings:
        """Update settings with partial data"""
        if self._settings is None:
            self._load_settings()
        
        # Only update fields that were actually provided
        update_data = updates.model_dump(exclude_unset=True)
        
        # Create new settings object with updates
        current_data = self._settings.model_dump()
        current_data.update(update_data)
        self._settings = Settings(**current_data)
        
        # Save to file
        self._save_settings()
        
        return self._settings
    
    def reset_settings(self) -> Settings:
        """Reset all settings to defaults"""
        self._settings = Settings()
        self._save_settings()
        return self._settings
    
    def export_settings(self) -> dict:
        """Export settings as dictionary"""
        if self._settings is None:
            self._load_settings()
        return self._settings.model_dump()
    
    def import_settings(self, settings_data: dict) -> Settings:
        """Import settings from dictionary"""
        try:
            self._settings = Settings(**settings_data)
            self._save_settings()
            return self._settings
        except ValueError as e:
            raise ValueError(f"Invalid settings data: {e}")