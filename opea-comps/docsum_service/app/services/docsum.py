import aiohttp
import logging
from bs4 import BeautifulSoup
from typing import Optional, Dict, Union
import os
import tempfile
from pathlib import Path
import magic
import pytesseract
from PIL import Image
import io
from youtube_transcript_api import YouTubeTranscriptApi
import pandas as pd
import json
from app.models import ContentType
from app.services.bedrock import BedrockService
from app.services.transcribe import TranscribeService

logger = logging.getLogger(__name__)

class Summarizer:
    def __init__(self):
        self.bedrock = BedrockService()
        self.transcribe = TranscribeService()
        self.supported_document_types = {
            ".txt", ".doc", ".docx", ".pdf",
            ".csv", ".json", ".xlsx", ".xls"
        }
        self.supported_image_types = {
            "image/jpeg", "image/png", "image/tiff"
        }
        self.supported_audio_types = {
            "audio/mpeg", "audio/wav", "audio/ogg"
        }
        self.supported_video_types = {
            "video/mp4", "video/mpeg", "video/ogg"
        }

    async def _fetch_url_content(self, url: str) -> Optional[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        return soup.get_text(separator=' ', strip=True)
                    else:
                        logger.error(f"Failed to fetch URL: {url}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return None

    async def _process_document(self, file_content: bytes, filename: str) -> Optional[str]:
        ext = Path(filename).suffix.lower()
        if ext not in self.supported_document_types:
            raise ValueError(f"Unsupported document type: {ext}")
        
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file.flush()
            
            try:
                if ext in {".csv", ".json", ".xlsx", ".xls"}:
                    if ext == ".json":
                        data = json.loads(file_content)
                        text = json.dumps(data, indent=2)
                    else:
                        df = pd.read_excel(temp_file.name) if ext in {".xlsx", ".xls"} else pd.read_csv(temp_file.name)
                        text = df.to_string()
                else:
                    # Use appropriate document processing library based on file type
                    # This is a placeholder - implement actual document processing
                    with open(temp_file.name, 'r', encoding='utf-8') as f:
                        text = f.read()
                return text
            finally:
                os.unlink(temp_file.name)

    async def _process_image(self, file_content: bytes) -> Optional[str]:
        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type not in self.supported_image_types:
            raise ValueError(f"Unsupported image type: {mime_type}")
        
        image = Image.open(io.BytesIO(file_content))
        text = pytesseract.image_to_string(image)
        return text if text.strip() else None

    async def _process_audio(self, file_content: bytes) -> Optional[str]:
        """Process audio file and return transcribed text."""
        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type not in self.supported_audio_types:
            raise ValueError(f"Unsupported audio type: {mime_type}")
        
        text = await self.transcribe.transcribe_audio(file_content, mime_type)
        return text if text else None

    async def _process_youtube(self, video_id: str) -> Optional[str]:
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            text = " ".join([entry["text"] for entry in transcript_list])
            return text
        except Exception as e:
            logger.error(f"Error getting YouTube transcript: {str(e)}")
            return None

    def _extract_youtube_id(self, url: str) -> Optional[str]:
        # Handle various YouTube URL formats
        if "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]
        elif "youtube.com/watch" in url:
            from urllib.parse import parse_qs, urlparse
            parsed_url = urlparse(url)
            return parse_qs(parsed_url.query).get("v", [None])[0]
        return None

    async def summarize(
        self,
        content: Union[str, bytes],
        content_type: ContentType,
        metadata: Optional[Dict] = None
    ) -> Optional[str]:
        try:
            text = None
            
            if content_type == ContentType.URL:
                text = await self._fetch_url_content(str(content))
            elif content_type == ContentType.TEXT:
                text = content
            elif content_type == ContentType.YOUTUBE:
                video_id = self._extract_youtube_id(str(content))
                if video_id:
                    text = await self._process_youtube(video_id)
            
            if text:
                return await self.bedrock.summarize(text)
            return None

        except Exception as e:
            logger.error(f"Error in summarize: {str(e)}")
            return None

    async def summarize_file(
        self,
        file_content: bytes,
        filename: str,
        content_type: ContentType
    ) -> Optional[str]:
        """Process uploaded file based on content type."""
        try:
            if content_type == ContentType.DOCUMENT:
                text = await self._process_document(file_content, filename)
            elif content_type == ContentType.IMAGE:
                text = await self._process_image(file_content)
            elif content_type == ContentType.AUDIO:
                text = await self._process_audio(file_content)
            elif content_type == ContentType.VIDEO:
                # For video, we use the same transcribe service
                text = await self._process_video(file_content)
            else:
                raise ValueError(f"Unsupported content type for file upload: {content_type}")

            if text:
                return await self.bedrock.summarize(text)
            return None

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            return None

    async def _process_video(self, file_content: bytes) -> Optional[str]:
        """Process video file and return transcribed text."""
        mime_type = magic.from_buffer(file_content, mime=True)
        if mime_type not in self.supported_video_types:
            raise ValueError(f"Unsupported video format: {mime_type}")
        
        text = await self.transcribe.transcribe_audio(file_content, mime_type)
        return text if text else None
