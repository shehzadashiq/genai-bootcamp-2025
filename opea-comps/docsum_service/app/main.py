from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.services.docsum import Summarizer
from app.services.vectorstore import VectorStore
from app.services.translator import TranslationService
from app.services.tts import TextToSpeechService
from app.models import ContentType, ContentInput, SummaryResponse
import logging
from typing import Optional
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

# Audio directory configuration
AUDIO_DIR = "/app/audio_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)
logger.info(f"Audio directory: {AUDIO_DIR}")

# Initialize services
summarizer = Summarizer()
vector_store = VectorStore()
translation_service = TranslationService()
tts_service = TextToSpeechService()

@app.get("/audio/{filename}")
async def get_audio_file(filename: str):
    """Serve audio files directly."""
    file_path = os.path.join(AUDIO_DIR, filename)
    logger.info(f"Attempting to serve audio file: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"Audio file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    try:
        with open(file_path, "rb") as f:
            content = f.read()
            
        logger.info(f"Successfully read audio file: {filename}")
        return Response(
            content=content,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Accept-Ranges": "bytes",
                "Cache-Control": "public, max-age=3600",
            }
        )
    except Exception as e:
        logger.error(f"Error serving audio file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize", response_model=SummaryResponse)
async def summarize_content(input_data: ContentInput):
    try:
        # Check cache first if enabled and URL is provided
        if input_data.use_cache and input_data.content_type == ContentType.URL:
            cached_result = await vector_store.get_summary(str(input_data.content))
            if cached_result:
                logger.info(f"Cache hit for URL: {input_data.content}")
                audio_paths = await tts_service.generate_all_audio({
                    "en": cached_result["summary"],
                    "ur": cached_result["translated_summary"]
                })
                cached_result.update({"audio_paths": audio_paths})
                return SummaryResponse(**cached_result)

        # Generate summary
        summary = await summarizer.summarize(
            content=input_data.content,
            content_type=input_data.content_type,
            metadata=input_data.metadata
        )
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
            "audio_paths": audio_paths,
            "metadata": input_data.metadata
        }

        # Store in cache if URL
        if input_data.use_cache and input_data.content_type == ContentType.URL:
            await vector_store.store_summary(
                str(input_data.content),
                result
            )
            logger.info(f"Stored summary in cache for URL: {input_data.content}")

        return SummaryResponse(**result)
    
    except Exception as e:
        logger.error(f"Error processing content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/summarize/file", response_model=SummaryResponse)
async def summarize_file(
    file: UploadFile = File(...),
    content_type: ContentType = Form(...),
    use_cache: bool = Form(True)
):
    try:
        file_content = await file.read()
        summary = await summarizer.summarize_file(
            file_content=file_content,
            filename=file.filename,
            content_type=content_type
        )
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

        return SummaryResponse(
            summary=summary,
            translated_summary=translated_summary,
            audio_paths=audio_paths,
            metadata={"filename": file.filename}
        )

    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
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
