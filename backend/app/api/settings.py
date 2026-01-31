from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.settings import Settings, SettingsUpdate
from app.services.settings import SettingsService

router = APIRouter()
settings_service = SettingsService()


@router.get("/settings", response_model=Settings)
async def get_settings():
    """Get current application settings"""
    return settings_service.get_settings()


@router.put("/settings", response_model=Settings)
async def update_settings(updates: SettingsUpdate):
    """Update application settings (partial update supported)"""
    try:
        return settings_service.update_settings(updates)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/settings/reset", response_model=Settings)
async def reset_settings():
    """Reset all settings to defaults"""
    return settings_service.reset_settings()


@router.get("/settings/export")
async def export_settings():
    """Export settings as JSON"""
    settings_data = settings_service.export_settings()
    return JSONResponse(
        content=settings_data,
        headers={
            "Content-Disposition": "attachment; filename=ytt-settings.json"
        }
    )


@router.post("/settings/import", response_model=Settings)
async def import_settings(settings_data: dict):
    """Import settings from JSON"""
    try:
        return settings_service.import_settings(settings_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))