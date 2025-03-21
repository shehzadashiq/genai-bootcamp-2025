from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn
from app.services.docsum import Summarizer
from app.services.vectorstore import VectorStore
from app.services.translator import TranslationService
from app.services.tts import TextToSpeechService
import logging
from typing import Optional, Dict
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Document Summary Service")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
summarizer = Summarizer()
vector_store = VectorStore()
translation_service = TranslationService()
tts_service = TextToSpeechService()

class URLInput(BaseModel):
    url: HttpUrl
    use_cache: bool = True

class SummaryResponse(BaseModel):
    summary: str
    translated_summary: str
    audio_paths: Dict[str, Optional[str]]

@app.post("/summarize", response_model=SummaryResponse)
async def summarize_url(input_data: URLInput):
    try:
        # Check cache first if enabled
        if input_data.use_cache:
            cached_result = await vector_store.get_summary(str(input_data.url))
            if cached_result:
                logger.info(f"Cache hit for URL: {input_data.url}")
                # Generate audio for cached result
                audio_paths = await tts_service.generate_all_audio({
                    "en": cached_result["summary"],
                    "ur": cached_result["translated_summary"]
                })
                cached_result.update(audio_paths)
                return SummaryResponse(
                    summary=cached_result["summary"],
                    translated_summary=cached_result["translated_summary"],
                    audio_paths=audio_paths
                )

        # Generate summary
        summary = await summarizer.summarize(str(input_data.url))
        if not summary:
            raise HTTPException(status_code=500, detail="Failed to generate summary")
        
        # Translate to Urdu
        translated_summary = await translation_service.translate_to_urdu(summary)
        if not translated_summary:
            raise HTTPException(status_code=500, detail="Failed to translate summary")
        
        # Generate audio for both languages
        audio_paths = await tts_service.generate_all_audio({
            "en": summary,
            "ur": translated_summary
        })

        # Prepare result
        result = {
            "summary": summary,
            "translated_summary": translated_summary,
            "audio_paths": audio_paths
        }

        # Store in cache
        if input_data.use_cache:
            await vector_store.store_summary(
                str(input_data.url),
                result
            )
            logger.info(f"Stored summary in cache for URL: {input_data.url}")

        return SummaryResponse(
            summary=result["summary"],
            translated_summary=result["translated_summary"],
            audio_paths=result["audio_paths"]
        )
    
    except Exception as e:
        logger.error(f"Error processing URL {input_data.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up services...")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down services...")
    # Clean up old audio files
    await tts_service.cleanup_old_audio()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
