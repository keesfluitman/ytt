import logging
import re
import json
from pathlib import Path
from typing import Optional, Dict, List
import asyncio
from app.config import settings
from app.services.history import HistoryService
from app.services.translator import TranslationService

logger = logging.getLogger(__name__)


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
            match = re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
            if match:
                return match.group(1)

        # Handle youtube.com URLs
        if "youtube.com" in url:
            match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
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
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0 and stdout:
                data = json.loads(stdout.decode())
                return {
                    "title": data.get("title", ""),
                    "duration": data.get("duration", 0),
                    "uploader": data.get("uploader", ""),
                    "upload_date": data.get("upload_date", ""),
                    "description": data.get("description", "")[:500],
                }
        except Exception as e:
            logger.error("Error getting video info: %s", e)

        return {}

    async def check_available_subtitles(
        self, url: str, use_cookies: str = "none"
    ) -> List[str]:
        """Check available subtitles for the video"""
        cmd = ["yt-dlp", "--list-subs", "--no-warnings", url]

        if use_cookies != "none":
            cmd.extend(["--cookies-from-browser", use_cookies])

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await result.communicate()

            if result.returncode == 0 and stdout:
                available = []
                lines = stdout.decode().split("\n")
                in_subtitles = False

                for line in lines:
                    if (
                        "Available automatic captions" in line
                        or "Available subtitles" in line
                    ):
                        in_subtitles = True
                        continue
                    if in_subtitles and line.strip():
                        parts = line.split()
                        if parts and not line.startswith("Language"):
                            lang_code = parts[0]
                            available.append(lang_code)

                return available
        except Exception as e:
            logger.error("Error checking subtitles: %s", e)

        return []

    async def fetch_transcript(
        self,
        url: str,
        language: str = "en",
        use_cookies: str = "none",
        auto_translate: bool = True,
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
            "--sub-lang",
            language,
            "--skip-download",
            "--sub-format",
            "vtt",
            "-o",
            str(self.temp_dir / "transcript"),
        ]

        if use_cookies != "none":
            cmd.extend(["--cookies-from-browser", use_cookies])

        cmd.append(url)

        try:
            result = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
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
            logger.error("Error fetching transcript: %s", e)

        return None

    def clean_vtt(self, vtt_content: str) -> str:
        """Clean VTT subtitle content to plain text"""
        lines = vtt_content.split("\n")
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
            if re.match(r"^\d+$", line):
                continue
            if re.match(r"^\d{2}:\d{2}", line):
                continue
            # Remove HTML tags
            line = re.sub(r"<[^>]+>", "", line)

            # Remove duplicate lines (common in auto-subs)
            if line and line not in seen:
                seen.add(line)
                clean_lines.append(line)

        return "\n".join(clean_lines)

    def prepare_text_for_translation(self, text: str) -> str:
        """Merge subtitle lines into readable paragraphs"""
        lines = text.split("\n")
        paragraphs = []
        current_para = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_para:
                    paragraphs.append(" ".join(current_para))
                    current_para = []
            else:
                if line and line[-1] in ".!?:;":
                    current_para.append(line)
                    if len(current_para) > 3:
                        paragraphs.append(" ".join(current_para))
                        current_para = []
                else:
                    current_para.append(line)

        if current_para:
            paragraphs.append(" ".join(current_para))

        return "\n\n".join(paragraphs)

    async def fetch_and_save_transcript(
        self,
        url: str,
        source_lang: str = "en",
        target_lang: Optional[str] = None,
        use_cookies: str = "none",
        merge_lines: bool = True,
    ) -> Dict:
        """Fetch transcript and translate via LibreTranslate"""
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        logger.info(
            "Fetching transcript for video %s (source=%s, target=%s)",
            video_id,
            source_lang,
            target_lang,
        )

        # Check for cached transcript first
        cached_transcript = self.history_service.get_youtube_transcript(
            video_id, source_lang, target_lang
        )

        if cached_transcript:
            logger.info("Returning cached transcript for video %s", video_id)
            result = {
                "video_id": video_id,
                "title": cached_transcript["title"],
                "url": url,
                "video_info": cached_transcript["video_info"],
                "available_languages": cached_transcript["available_languages"],
                "source_lang": source_lang,
                "source_transcript_raw": cached_transcript["original_text"],
                "source_transcript_processed": self.prepare_text_for_translation(
                    cached_transcript["original_text"]
                )
                if merge_lines
                else None,
                "target_lang": target_lang,
                "target_transcript_raw": cached_transcript["translated_text"]
                if cached_transcript["translated_text"]
                else None,
                "target_transcript_processed": self.prepare_text_for_translation(
                    cached_transcript["translated_text"]
                )
                if cached_transcript["translated_text"] and merge_lines
                else None,
                "cached": True,
                "entry_id": cached_transcript["entry_id"],
                "translation_error": None,
                "folder_path": video_id,
            }
            return result

        # Get video info
        video_info = await self.get_video_info(url, use_cookies)
        title = video_info.get("title", video_id)
        logger.info("Video title: %s", title)

        # Check available subtitles
        available_subs = await self.check_available_subtitles(url, use_cookies)
        logger.info(
            "Available subtitles: %s", available_subs[:10] if available_subs else "none"
        )

        # Fetch source language transcript
        source_transcript_raw = await self.fetch_transcript(
            url, source_lang, use_cookies
        )
        if not source_transcript_raw:
            raise ValueError(f"Could not fetch transcript for language '{source_lang}'")

        logger.info("Fetched source transcript: %d chars", len(source_transcript_raw))

        # Process transcript if requested
        source_transcript_processed = None
        if source_transcript_raw and merge_lines:
            source_transcript_processed = self.prepare_text_for_translation(
                source_transcript_raw
            )

        # Handle target language translation — always via LibreTranslate
        target_transcript_raw = None
        target_transcript_processed = None
        translation_provider = None
        translation_error = None

        if target_lang and target_lang != source_lang:
            logger.info(
                "Translating from %s to %s via LibreTranslate", source_lang, target_lang
            )

            # Use the processed version for better translation quality
            text_to_translate = source_transcript_processed or source_transcript_raw

            try:
                translation_result = await self.translation_service.translate(
                    text=text_to_translate,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    provider="libretranslate",
                )

                target_transcript_raw = translation_result["translatedText"]
                target_transcript_processed = translation_result["translatedText"]
                translation_provider = "libretranslate"
                logger.info(
                    "Successfully translated to %s (%d chars)",
                    target_lang,
                    len(target_transcript_raw),
                )

            except Exception as e:
                translation_error = f"Translation failed: {str(e)}"
                logger.error("Failed to translate to %s: %s", target_lang, e)

        # Save to history
        actual_target_lang = (
            target_lang
            if target_lang and target_lang != source_lang and target_transcript_raw
            else None
        )

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
            provider=translation_provider or "libretranslate",
            folder_path=video_id,
        )

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
            "cached": False,
            "entry_id": entry_id,
            "translation_error": translation_error,
            "folder_path": video_id,
        }

        # Save files to entry subfolder
        entry_folder = self.get_entry_folder(video_id)

        # Write source transcript
        source_file = entry_folder / f"transcript_{source_lang}.txt"
        source_file.write_text(source_transcript_raw)
        logger.info("Saved source transcript to %s", source_file)

        # Write translation if available
        if target_transcript_raw:
            translation_file = entry_folder / f"translation_{target_lang}.txt"
            translation_file.write_text(target_transcript_raw)
            logger.info("Saved translation to %s", translation_file)

        # Write metadata
        meta_file = entry_folder / "meta.json"
        meta_file.write_text(json.dumps(result, indent=2, ensure_ascii=False))
        logger.info("Saved metadata to %s", meta_file)

        return result

    def sanitize_filename(self, name: str) -> str:
        """Make a string safe for use as filename"""
        # Remove or replace invalid characters
        name = re.sub(r'[<>:"/\\|?*]', "", name)
        name = re.sub(r"\s+", "_", name)
        return name[:80]  # Limit length

    def get_entry_folder(self, video_id: str) -> Path:
        """Get or create the subfolder for a video entry"""
        folder = self.transcript_dir / video_id
        folder.mkdir(exist_ok=True)
        return folder

    def save_translation_to_folder(
        self, video_id: str, target_lang: str, translated_text: str
    ):
        """Write a translation file to an existing entry's folder and update meta.json"""
        folder = self.get_entry_folder(video_id)

        # Write translation file
        translation_file = folder / f"translation_{target_lang}.txt"
        translation_file.write_text(translated_text)
        logger.info("Saved translation to %s", translation_file)

        # Update meta.json if it exists
        meta_file = folder / "meta.json"
        if meta_file.exists():
            try:
                meta = json.loads(meta_file.read_text())
                meta["target_transcript_raw"] = translated_text
                meta["target_transcript_processed"] = translated_text
                meta["target_lang"] = target_lang
                meta["translation_error"] = None
                meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
                logger.info("Updated meta.json in %s", folder)
            except Exception as e:
                logger.warning("Failed to update meta.json: %s", e)
