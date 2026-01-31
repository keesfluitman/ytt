import subprocess
import re
import json
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import asyncio
from app.config import settings
from app.services.history import HistoryService
from app.services.translator import TranslationService


class YouTubeTranscriptService:
    def __init__(self):
        self.transcript_dir = settings.TRANSCRIPT_DIR
        self.transcript_dir.mkdir(exist_ok=True)
        self.temp_dir = self.transcript_dir / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        self.history_service = HistoryService()
        self.translation_service = TranslationService()
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        # Handle youtu.be URLs
        if "youtu.be/" in url:
            match = re.search(r'youtu\.be/([a-zA-Z0-9_-]{11})', url)
            if match:
                return match.group(1)
        
        # Handle youtube.com URLs
        if "youtube.com" in url:
            match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
            if match:
                return match.group(1)
        
        return None
    
    async def get_video_info(self, url: str, use_cookies: str = "none") -> Dict:
        """Get video title and metadata using yt-dlp"""
        cmd = ["yt-dlp", "--dump-json", "--no-warnings", url]
        
        if use_cookies != "none":
            cmd.extend(["--cookies-from-browser", use_cookies])
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and stdout:
                data = json.loads(stdout.decode())
                return {
                    "title": data.get("title", ""),
                    "duration": data.get("duration", 0),
                    "uploader": data.get("uploader", ""),
                    "upload_date": data.get("upload_date", ""),
                    "description": data.get("description", "")[:500]
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
        
        return {}
    
    async def check_available_subtitles(self, url: str, use_cookies: str = "none") -> List[str]:
        """Check available subtitles for the video"""
        cmd = ["yt-dlp", "--list-subs", "--no-warnings", url]
        
        if use_cookies != "none":
            cmd.extend(["--cookies-from-browser", use_cookies])
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and stdout:
                available = []
                lines = stdout.decode().split('\n')
                in_subtitles = False
                
                for line in lines:
                    if 'Available automatic captions' in line or 'Available subtitles' in line:
                        in_subtitles = True
                        continue
                    if in_subtitles and line.strip():
                        parts = line.split()
                        if parts and not line.startswith('Language'):
                            lang_code = parts[0]
                            available.append(lang_code)
                
                return available
        except Exception as e:
            print(f"Error checking subtitles: {e}")
        
        return []
    
    async def fetch_transcript(
        self, 
        url: str, 
        language: str = "en",
        use_cookies: str = "none",
        auto_translate: bool = True
    ) -> Optional[str]:
        """Fetch transcript for a specific language"""
        # Clean temp directory
        for f in self.temp_dir.glob("*"):
            f.unlink()
        
        # Build yt-dlp command
        cmd = [
            "yt-dlp",
            "--write-sub",
            "--write-auto-sub",
            "--sub-lang", language,
            "--skip-download",
            "--sub-format", "vtt",
            "-o", str(self.temp_dir / "transcript"),
        ]
        
        if use_cookies != "none":
            cmd.extend(["--cookies-from-browser", use_cookies])
        
        cmd.append(url)
        
        try:
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()
            
            # Find VTT file
            vtt_files = list(self.temp_dir.glob(f"*.{language}.vtt"))
            if not vtt_files:
                vtt_files = list(self.temp_dir.glob("*.vtt"))
            
            if vtt_files:
                vtt_content = vtt_files[0].read_text()
                return self.clean_vtt(vtt_content)
        except Exception as e:
            print(f"Error fetching transcript: {e}")
        
        return None
    
    def clean_vtt(self, vtt_content: str) -> str:
        """Clean VTT subtitle content to plain text"""
        lines = vtt_content.split('\n')
        clean_lines = []
        seen = set()
        
        for line in lines:
            line = line.strip()
            # Skip metadata, timestamps, and empty lines
            if not line:
                continue
            if line == "WEBVTT":
                continue
            if line.startswith("Kind:") or line.startswith("Language:"):
                continue
            if "-->" in line:
                continue
            if re.match(r'^\d+$', line):
                continue
            if re.match(r'^\d{2}:\d{2}', line):
                continue
            # Remove HTML tags
            line = re.sub(r'<[^>]+>', '', line)
            
            # Remove duplicate lines (common in auto-subs)
            if line and line not in seen:
                seen.add(line)
                clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    def prepare_text_for_translation(self, text: str) -> str:
        """Merge subtitle lines into readable paragraphs"""
        lines = text.split('\n')
        paragraphs = []
        current_para = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if current_para:
                    paragraphs.append(' '.join(current_para))
                    current_para = []
            else:
                if line and line[-1] in '.!?:;':
                    current_para.append(line)
                    if len(current_para) > 3:
                        paragraphs.append(' '.join(current_para))
                        current_para = []
                else:
                    current_para.append(line)
        
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        return '\n\n'.join(paragraphs)
    
    async def fetch_and_save_transcript(
        self,
        url: str,
        source_lang: str = "en",
        target_lang: Optional[str] = None,
        use_cookies: str = "none",
        merge_lines: bool = True
    ) -> Dict:
        """Fetch transcripts and save them"""
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
        
        # Check for cached transcript first
        cached_transcript = self.history_service.get_youtube_transcript(
            video_id, source_lang, target_lang
        )
        
        if cached_transcript:
            # Return cached version with additional processing if needed
            result = {
                "video_id": video_id,
                "title": cached_transcript["title"],
                "url": url,
                "video_info": cached_transcript["video_info"],
                "available_languages": cached_transcript["available_languages"],
                "source_lang": source_lang,
                "source_transcript_raw": cached_transcript["original_text"],
                "source_transcript_processed": self.prepare_text_for_translation(cached_transcript["original_text"]) if merge_lines else None,
                "target_lang": target_lang,
                "target_transcript_raw": cached_transcript["translated_text"] if cached_transcript["translated_text"] else None,
                "target_transcript_processed": self.prepare_text_for_translation(cached_transcript["translated_text"]) if cached_transcript["translated_text"] and merge_lines else None,
                "cached": True,
                "entry_id": cached_transcript["entry_id"]
            }
            return result
        
        # Get video info
        video_info = await self.get_video_info(url, use_cookies)
        title = video_info.get("title", video_id)
        
        # Check available subtitles
        available_subs = await self.check_available_subtitles(url, use_cookies)
        
        # Fetch source language transcript
        source_transcript_raw = await self.fetch_transcript(url, source_lang, use_cookies)
        if not source_transcript_raw:
            raise ValueError(f"Could not fetch transcript for language '{source_lang}'")
        
        # Process transcript if requested
        source_transcript_processed = None
        if source_transcript_raw and merge_lines:
            source_transcript_processed = self.prepare_text_for_translation(source_transcript_raw)
        
        # Handle target language translation
        target_transcript_raw = None
        target_transcript_processed = None
        translation_provider = None
        
        if target_lang and target_lang != source_lang:
            # First, check if YouTube has subtitles in target language
            if target_lang in available_subs or f"{target_lang}-{source_lang}" in available_subs:
                # Use YouTube's subtitles if available
                target_transcript_raw = await self.fetch_transcript(url, target_lang, use_cookies)
                if target_transcript_raw and merge_lines:
                    target_transcript_processed = self.prepare_text_for_translation(target_transcript_raw)
                translation_provider = "youtube"
            else:
                # Use LibreTranslate to translate the source transcript
                print(f"YouTube doesn't have {target_lang} subtitles, using LibreTranslate...")
                
                # Use the processed version for translation for better quality
                text_to_translate = source_transcript_processed or source_transcript_raw
                
                try:
                    translation_result = await self.translation_service.translate(
                        text=text_to_translate,
                        source_lang=source_lang,
                        target_lang=target_lang,
                        provider="libretranslate"
                    )
                    
                    # Store the translated text
                    target_transcript_raw = translation_result["translatedText"]
                    target_transcript_processed = translation_result["translatedText"]
                    translation_provider = "libretranslate"
                    print(f"Successfully translated to {target_lang} using LibreTranslate")
                    
                except Exception as e:
                    print(f"Error translating with LibreTranslate: {e}")
                    # Continue without translation rather than failing
        
        # Save to history
        # Only set target_lang if we actually have a different target language with translation
        actual_target_lang = target_lang if target_lang and target_lang != source_lang and target_transcript_raw else None
        
        entry_id = self.history_service.add_transcript_entry(
            video_id=video_id,
            title=title,
            url=url,
            original_text=source_transcript_raw,
            source_lang=source_lang,
            available_languages=available_subs,
            video_info=video_info,
            translated_text=target_transcript_raw,
            target_lang=actual_target_lang,
            provider=translation_provider if translation_provider else "youtube"
        )
        
        # Also save files (for backup/debugging)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        safe_title = self.sanitize_filename(title)
        
        result = {
            "video_id": video_id,
            "title": title,
            "url": url,
            "video_info": video_info,
            "available_languages": available_subs,
            "source_lang": source_lang,
            "source_transcript_raw": source_transcript_raw,
            "source_transcript_processed": source_transcript_processed,
            "target_lang": target_lang,
            "target_transcript_raw": target_transcript_raw,
            "target_transcript_processed": target_transcript_processed,
            "timestamp": timestamp,
            "cached": False,
            "entry_id": entry_id
        }
        
        # Save metadata file (for backup)
        meta_file = self.transcript_dir / f"{safe_title}_{timestamp}_meta.json"
        meta_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        
        # Save transcript files (for backup)
        if source_transcript_raw:
            source_file = self.transcript_dir / f"{safe_title}_{timestamp}_{source_lang}.txt"
            source_file.write_text(source_transcript_raw)
            result["source_file"] = str(source_file)
        
        if target_transcript_raw:
            target_file = self.transcript_dir / f"{safe_title}_{timestamp}_{target_lang}.txt"
            target_file.write_text(target_transcript_raw)
            result["target_file"] = str(target_file)
        
        return result
    
    def sanitize_filename(self, name: str) -> str:
        """Make a string safe for use as filename"""
        # Remove or replace invalid characters
        name = re.sub(r'[<>:"/\\|?*]', '', name)
        name = re.sub(r'\s+', '_', name)
        return name[:80]  # Limit length