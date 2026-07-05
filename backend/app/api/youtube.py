from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from pydantic import BaseModel

from app.services.youtube import YouTubeTranscriptService

router = APIRouter()
youtube_service = YouTubeTranscriptService()


class YouTubeTranscriptRequest(BaseModel):
    url: str
    source_lang: str = "en"
    target_lang: Optional[str] = None
    use_cookies: str = "none"  # none, firefox, chrome
    merge_lines: bool = True  # Whether to merge subtitle lines into paragraphs

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "source_lang": "en",
                "target_lang": "de",
                "use_cookies": "firefox",
                "merge_lines": True,
            }
        }


class YouTubeInfoRequest(BaseModel):
    url: str
    use_cookies: str = "none"


@router.post("/youtube/fetch")
async def fetch_youtube_transcript(request: YouTubeTranscriptRequest):
    """Fetch transcript from YouTube video"""
    try:
        result = await youtube_service.fetch_and_save_transcript(
            url=request.url,
            source_lang=request.source_lang,
            target_lang=request.target_lang,
            use_cookies=request.use_cookies,
            merge_lines=request.merge_lines,
        )

        # Return both raw and processed transcripts
        response = {
            "video_id": result["video_id"],
            "title": result["title"],
            "url": result["url"],
            "video_info": result["video_info"],
            "available_languages": result["available_languages"],
            "source_lang": result["source_lang"],
            "source_transcript_raw": result["source_transcript_raw"],
            "source_transcript_processed": result["source_transcript_processed"],
            "target_lang": result["target_lang"],
            "target_transcript_raw": result["target_transcript_raw"],
            "target_transcript_processed": result["target_transcript_processed"],
            "entry_id": result.get("entry_id"),
            "cached": result.get("cached", False),
            "translation_error": result.get("translation_error"),
        }

        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error fetching transcript: {str(e)}"
        )


@router.post("/youtube/info")
async def get_youtube_video_info(request: YouTubeInfoRequest):
    """Get YouTube video information and available subtitles"""
    video_id = youtube_service.extract_video_id(request.url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    try:
        video_info = await youtube_service.get_video_info(
            request.url, request.use_cookies
        )
        available_subs = await youtube_service.check_available_subtitles(
            request.url, request.use_cookies
        )

        return {
            "video_id": video_id,
            "video_info": video_info,
            "available_subtitles": available_subs,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting video info: {str(e)}"
        )


@router.get("/youtube/extract-id")
async def extract_video_id(url: str = Query(..., description="YouTube URL")):
    """Extract video ID from YouTube URL"""
    video_id = youtube_service.extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")

    return {"video_id": video_id, "url": url}


@router.get("/youtube/channel")
async def list_channel_videos(
    handle: Optional[str] = Query(None, description="Channel handle, e.g. @WebDevSimplified"),
    channel_id: Optional[str] = Query(None, description="Channel ID, e.g. UC..."),
    url: Optional[str] = Query(None, description="Full channel/playlist URL"),
    limit: int = Query(0, ge=0, description="Max videos (0 = full catalog)"),
):
    """Enumerate a channel's uploads (video id + title) via yt-dlp flat-playlist.

    Provide exactly one of handle / channel_id / url. Fast — does not fetch
    per-video pages, so it's meant for searching over titles, not summarizing.
    """
    if url:
        channel_url = url
    elif channel_id:
        channel_url = f"https://www.youtube.com/channel/{channel_id}/videos"
    elif handle:
        h = handle if handle.startswith("@") else f"@{handle}"
        channel_url = f"https://www.youtube.com/{h}/videos"
    else:
        raise HTTPException(
            status_code=400, detail="Provide one of: handle, channel_id, url"
        )

    try:
        videos = await youtube_service.list_channel_videos(channel_url, limit=limit)
        return {"channel_url": channel_url, "count": len(videos), "videos": videos}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error enumerating channel: {str(e)}"
        )
