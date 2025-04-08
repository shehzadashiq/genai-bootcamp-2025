from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from services.listening_service import ListeningService
import re
from urllib.parse import urlparse, parse_qs
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter()
listening_service = ListeningService()

class VideoURL(BaseModel):
    url: str

class TranscriptResponse(BaseModel):
    transcript: Optional[str] = None
    error: Optional[str] = None
    statistics: Optional[Dict] = None

class QuestionsResponse(BaseModel):
    questions: Optional[List[Dict]] = None
    error: Optional[str] = None

def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from YouTube URL."""
    logger.info(f"Extracting video ID from URL: {url}")
    try:
        # Handle empty URL
        if not url:
            logger.error("Empty URL provided")
            return None
            
        # If it's already just the video ID (11 characters)
        if re.match(r'^[A-Za-z0-9_-]{11}$', url):
            logger.info(f"URL is already a video ID: {url}")
            return url
            
        # Clean up the URL first
        url = url.strip()
        if url.endswith('&'):
            url = url[:-1]
            
        # Try to parse URL
        parsed_url = urlparse(url)
        logger.debug(f"Parsed URL - netloc: {parsed_url.netloc}, path: {parsed_url.path}, query: {parsed_url.query}")
        
        # Handle youtube.com URLs
        if 'youtube.com' in parsed_url.netloc:
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params:
                video_id = query_params['v'][0].split('&')[0]
                logger.info(f"Found video ID in query params: {video_id}")
                return video_id
                
        # Handle youtu.be URLs
        elif 'youtu.be' in parsed_url.netloc:
            video_id = parsed_url.path.strip('/').split('&')[0]
            logger.info(f"Found video ID in youtu.be path: {video_id}")
            return video_id
            
        # Try regex patterns as fallback
        patterns = [
            r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})',
            r'youtube\.com\/watch\?.*v=([^"&?\/\s]{11})',
            r'youtube\.com\/embed\/([^"&?\/\s]{11})',
            r'youtube\.com\/v\/([^"&?\/\s]{11})',
            r'youtu\.be\/([^"&?\/\s]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.info(f"Found video ID using regex: {video_id}")
                return video_id
                
        logger.error(f"Could not extract video ID from URL: {url}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting video ID: {e}")
        return None

@router.post("/api/listening/transcript")
async def get_transcript(video: VideoURL) -> TranscriptResponse:
    """Get transcript for a video."""
    logger.info(f"[/api/listening/transcript] Received URL: {video.url}")
    try:
        video_id = extract_video_id(video.url)
        if not video_id:
            logger.error(f"[/api/listening/transcript] Could not extract video ID from URL: {video.url}")
            return TranscriptResponse(error="Invalid YouTube URL")
            
        logger.info(f"[/api/listening/transcript] Extracted video ID: {video_id}")
        result = listening_service.get_transcript_with_stats(video.url)
        if isinstance(result, dict) and "error" in result:
            logger.error(f"[/api/listening/transcript] Error getting transcript for video ID: {video_id}")
            return TranscriptResponse(error=result["error"])
            
        # Extract transcript text from segments
        transcript_text = " ".join([segment["text"] for segment in result["transcript"]])
        logger.info(f"[/api/listening/transcript] Successfully retrieved transcript for video ID: {video_id}")
        return TranscriptResponse(transcript=transcript_text, statistics=result.get("statistics"))
    except Exception as e:
        logger.error(f"[/api/listening/transcript] Error getting transcript: {str(e)}")
        return TranscriptResponse(error=str(e))

@router.post("/api/listening/download-transcript")
async def download_transcript(video: VideoURL) -> TranscriptResponse:
    """Download and cache transcript."""
    logger.info(f"[/api/listening/download-transcript] Received URL: {video.url}")
    try:
        video_id = extract_video_id(video.url)
        if not video_id:
            logger.error(f"[/api/listening/download-transcript] Could not extract video ID from URL: {video.url}")
            return TranscriptResponse(error="Invalid YouTube URL")
            
        logger.info(f"[/api/listening/download-transcript] Extracted video ID: {video_id}")
        transcript = listening_service.get_transcript(video.url)
        if not transcript:
            logger.error(f"[/api/listening/download-transcript] No transcript found for video ID: {video_id}")
            return TranscriptResponse(error="No transcript available")
            
        logger.info(f"[/api/listening/download-transcript] Successfully downloaded transcript for video ID: {video_id}")
        listening_service.store_transcript(video.url, transcript)
        return TranscriptResponse(transcript=transcript)
    except Exception as e:
        logger.error(f"[/api/listening/download-transcript] Error downloading transcript: {str(e)}")
        return TranscriptResponse(error=str(e))

@router.post("/api/listening/questions")
async def generate_questions(video: VideoURL) -> QuestionsResponse:
    """Generate questions from transcript."""
    logger.info(f"[/api/listening/questions] Received URL: {video.url}")
    try:
        video_id = extract_video_id(video.url)
        if not video_id:
            logger.error(f"[/api/listening/questions] Could not extract video ID from URL: {video.url}")
            return QuestionsResponse(error="Invalid YouTube URL")
            
        logger.info(f"[/api/listening/questions] Extracted video ID: {video_id}")
        result = listening_service.get_questions_for_video(video.url)
        if "error" in result:
            logger.error(f"[/api/listening/questions] Error generating questions for video ID: {video_id}")
            return QuestionsResponse(error=result["error"])
            
        # Log questions for debugging
        if "questions" in result:
            for i, q in enumerate(result["questions"]):
                logger.info(f"Question {i}: {json.dumps(q, ensure_ascii=False)}")
                
        logger.info(f"[/api/listening/questions] Successfully generated questions for video ID: {video_id}")
        return QuestionsResponse(questions=result["questions"])
    except Exception as e:
        logger.error(f"[/api/listening/questions] Error generating questions: {str(e)}")
        return QuestionsResponse(error=str(e))
