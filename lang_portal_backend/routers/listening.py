from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from services.listening_service import ListeningService

router = APIRouter()
listening_service = ListeningService()

class VideoURL(BaseModel):
    url: str

class TranscriptResponse(BaseModel):
    video_id: str
    message: str

class Question(BaseModel):
    id: int
    text: str
    options: List[str]
    correct_answer: str
    audio_start: float
    audio_end: float

class QuestionsResponse(BaseModel):
    questions: Optional[List[Question]] = None
    error: Optional[str] = None

@router.post("/listening/download-transcript")
async def download_transcript(video: VideoURL) -> TranscriptResponse:
    try:
        video_id = listening_service.extract_video_id(video.url)
        transcript = listening_service.get_transcript(video.url)
        listening_service.store_transcript(video.url, transcript)
        return TranscriptResponse(
            video_id=video_id,
            message="Transcript downloaded and stored successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/listening/questions")
async def get_listening_questions(video: VideoURL) -> QuestionsResponse:
    try:
        result = listening_service.get_questions_for_video(video.url)
        if "error" in result:
            return QuestionsResponse(error=result["error"])
        return QuestionsResponse(questions=result["questions"])
    except Exception as e:
        return QuestionsResponse(error=str(e))

@router.post("/listening/transcript")
async def get_transcript_and_stats(video: VideoURL) -> Dict:
    try:
        result = listening_service.get_transcript_with_stats(video.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
