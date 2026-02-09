import logging
import httpx
from typing import Optional, Dict, Any
import asyncio
from app.config import settings

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self):
        self.libretranslate_url = settings.LIBRETRANSLATE_URL
        self.api_key = settings.LIBRETRANSLATE_API_KEY
        self.chunk_size = settings.CHUNK_SIZE

    async def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "en",
        provider: str = "libretranslate",
    ) -> Dict[str, Any]:
        logger.info(
            "Translating %d chars from '%s' to '%s' via %s",
            len(text),
            source_lang,
            target_lang,
            provider,
        )
        if provider == "libretranslate":
            return await self._translate_libretranslate(text, source_lang, target_lang)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    async def _translate_libretranslate(
        self, text: str, source_lang: str, target_lang: str
    ) -> Dict[str, Any]:
        if len(text) > self.chunk_size:
            chunks = self._split_text(text)
            translated_chunks = []

            for chunk in chunks:
                result = await self._call_libretranslate(
                    chunk, source_lang, target_lang
                )
                translated_chunks.append(result["translatedText"])

            return {
                "translatedText": "\n\n".join(translated_chunks),
                "detectedLanguage": source_lang if source_lang != "auto" else None,
            }
        else:
            return await self._call_libretranslate(text, source_lang, target_lang)

    async def _call_libretranslate(
        self, text: str, source_lang: str, target_lang: str
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            payload = {
                "q": text,
                "source": source_lang,
                "target": target_lang,
                "format": "text",
            }

            if self.api_key:
                payload["api_key"] = self.api_key

            try:
                response = await client.post(
                    f"{self.libretranslate_url}/translate", json=payload
                )
                response.raise_for_status()
                logger.info(
                    "LibreTranslate translation successful (%s -> %s)",
                    source_lang,
                    target_lang,
                )
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error("LibreTranslate HTTP error: %s", e.response.status_code)
                raise Exception(f"LibreTranslate error: {e.response.status_code}")
            except Exception as e:
                logger.error("LibreTranslate connection failed: %s", e)
                raise Exception(f"Translation failed: {str(e)}")

    async def detect_language(self, text: str) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {"q": text[:1000]}

            if self.api_key:
                payload["api_key"] = self.api_key

            try:
                response = await client.post(
                    f"{self.libretranslate_url}/detect", json=payload
                )
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise Exception(f"Language detection failed: {str(e)}")

    async def get_supported_languages(self) -> list:
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(f"{self.libretranslate_url}/languages")
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise Exception(f"Failed to fetch languages: {str(e)}")

    def _split_text(self, text: str) -> list:
        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 < self.chunk_size:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph

        if current_chunk:
            chunks.append(current_chunk)

        return chunks

    def prepare_text_for_translation(self, text: str) -> str:
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
