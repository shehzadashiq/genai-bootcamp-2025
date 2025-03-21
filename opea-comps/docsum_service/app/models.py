from enum import Enum
from pydantic import BaseModel, HttpUrl
from typing import Dict, Optional, Union

class ContentType(str, Enum):
    URL = "url"
    TEXT = "text"
    DOCUMENT = "document"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    YOUTUBE = "youtube"
    DATASET = "dataset"

class ContentInput(BaseModel):
    content_type: ContentType
    content: Union[HttpUrl, str]
    use_cache: bool = True
    metadata: Optional[Dict] = None

class SummaryResponse(BaseModel):
    summary: str
    translated_summary: str
    audio_paths: Dict[str, Optional[str]]
    metadata: Optional[Dict] = None
