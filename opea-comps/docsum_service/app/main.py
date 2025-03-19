from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
import uvicorn
from app.services.docsum import DocSumService
from app.services.vectorstore import VectorStore
from app.services.translator import TranslationService
from app.services.tts import TextToSpeechService
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

# Initialize services
docsum_service = DocSumService()
vector_store = VectorStore()
translation_service = TranslationService()
tts_service = TextToSpeechService()

class URLInput(BaseModel):
    url: HttpUrl
    use_cache: bool = True

class SummaryResponse(BaseModel):
    summary: str
    translated_summary: str
    audio_url: Optional[str]

@app.post("/summarize", response_model=SummaryResponse)
async def summarize_url(input_data: URLInput):
    try:
        # Check cache first if enabled
        if input_data.use_cache:
            cached_result = await vector_store.get_summary(str(input_data.url))
            if cached_result:
                logger.info(f"Cache hit for URL: {input_data.url}")
                return cached_result

        # Generate summary
        summary = await docsum_service.generate_summary(str(input_data.url))
        
        # Translate to Urdu
        translated_summary = await translation_service.translate_to_urdu(summary)
        
        # Generate audio
        audio_url = await tts_service.generate_audio(translated_summary)
        
        # Store in cache
        if input_data.use_cache:
            await vector_store.store_summary(
                str(input_data.url),
                summary,
                translated_summary,
                audio_url
            )
        
        return SummaryResponse(
            summary=summary,
            translated_summary=translated_summary,
            audio_url=audio_url
        )
    
    except Exception as e:
        logger.error(f"Error processing URL {input_data.url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)
