import re
from pathlib import Path
from typing import Optional, Tuple
import aiofiles
import chardet
from fastapi import UploadFile
import pdfplumber
from docx import Document
import json
import yaml


class FileHandler:
    def __init__(self):
        self.supported_formats = ['.txt', '.srt', '.vtt', '.md', '.docx', '.pdf', '.json', '.yaml', '.yml']
    
    async def extract_text(self, file: UploadFile) -> Tuple[str, str]:
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext in ['.txt', '.md']:
            return await self._extract_plain_text(file)
        elif file_ext in ['.srt', '.vtt']:
            return await self._extract_subtitle(file)
        elif file_ext == '.pdf':
            return await self._extract_pdf(file)
        elif file_ext == '.docx':
            return await self._extract_docx(file)
        elif file_ext in ['.json', '.yaml', '.yml']:
            return await self._extract_structured(file)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    async def _extract_plain_text(self, file: UploadFile) -> Tuple[str, str]:
        content = await file.read()
        
        detected = chardet.detect(content)
        encoding = detected['encoding'] or 'utf-8'
        
        try:
            text = content.decode(encoding)
        except UnicodeDecodeError:
            text = content.decode('latin-1')
        
        return text, "text"
    
    async def _extract_subtitle(self, file: UploadFile) -> Tuple[str, str]:
        content = await file.read()
        text = content.decode('utf-8', errors='ignore')
        
        clean_text = self.clean_subtitle(text)
        return clean_text, "subtitle"
    
    def clean_subtitle(self, subtitle_content: str) -> str:
        lines = subtitle_content.split('\n')
        clean_lines = []
        seen = set()
        
        for line in lines:
            line = line.strip()
            
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
            
            line = re.sub(r'<[^>]+>', '', line)
            
            if line and line not in seen:
                seen.add(line)
                clean_lines.append(line)
        
        return '\n'.join(clean_lines)
    
    async def _extract_pdf(self, file: UploadFile) -> Tuple[str, str]:
        content = await file.read()
        text = []
        
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        
        return '\n\n'.join(text), "pdf"
    
    async def _extract_docx(self, file: UploadFile) -> Tuple[str, str]:
        content = await file.read()
        doc = Document(io.BytesIO(content))
        
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        
        return '\n\n'.join(text), "docx"
    
    async def _extract_structured(self, file: UploadFile) -> Tuple[str, str]:
        content = await file.read()
        text = content.decode('utf-8', errors='ignore')
        
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext == '.json':
            data = json.loads(text)
            return json.dumps(data, indent=2, ensure_ascii=False), "json"
        else:
            data = yaml.safe_load(text)
            return yaml.dump(data, allow_unicode=True, default_flow_style=False), "yaml"
    
    async def save_file(self, file: UploadFile, directory: Path) -> Path:
        file_path = directory / file.filename
        
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        return file_path
    
    def format_output(self, text: str, format: str) -> str:
        if format == "markdown":
            return self._to_markdown(text)
        elif format == "html":
            return self._to_html(text)
        else:
            return text
    
    def _to_markdown(self, text: str) -> str:
        paragraphs = text.split('\n\n')
        return '\n\n'.join(paragraphs)
    
    def _to_html(self, text: str) -> str:
        paragraphs = text.split('\n\n')
        html_paragraphs = [f"<p>{p}</p>" for p in paragraphs]
        return '\n'.join(html_paragraphs)


import io