# Flashcards Learning Game

## Business Goal

Learn Urdu words and their English translations through an interactive flashcards game.

Create a curated database of the top 1000 most common Urdu words and their English translations using existing Word model data.

## Implementation Details

### Frontend Features
- The flashcard interface displays Urdu words and their English translations
- Click on the card or press the space button to flip it
- The back of the flashcard shows:
    - English translation
    - Example sentence in Urdu text
    - Word information (verb, noun, adjective, etc.)
    - Etymology information if available
- Navigation:
    - Back button to return to study activities page
    - Play/Pause button to automatically go through the flashcards with configurable speed
    - Previous/Next buttons to navigate between cards
    - Random button to randomize the existing cards
    - Settings button to:
        - Control the playback speed for auto-play
        - Toggle the Urdu transcription visibility
    - Fullscreen button to maximize the learning experience
    - Restart button to begin a new game

### Technical Implementation

#### Text-to-Speech Service
The application uses Google Cloud Text-to-Speech for audio synthesis:
- Language: Urdu (ur-PK)
- Voice Type: Standard
- Gender: Female
- Sample Rate: 24000 Hz
- Audio Encoding: MP3

Implementation Details:
1. TTS Service (`api/services/tts.py`):
   ```python
   class TTSService:
       def __init__(self):
           self.client = texttospeech.TextToSpeechClient()
           self.voice = texttospeech.VoiceSelectionParams(
               language_code="ur-PK",
               name="ur-PK-Standard-A"
           )
           self.audio_config = texttospeech.AudioConfig(
               audio_encoding=texttospeech.AudioEncoding.MP3,
               sample_rate_hertz=24000
           )

       async def synthesize_speech(self, text: str) -> bytes:
           synthesis_input = texttospeech.SynthesisInput(text=text)
           response = await self.client.synthesize_speech(
               input=synthesis_input,
               voice=self.voice,
               audio_config=self.audio_config
           )
           return response.audio_content
   ```

2. Audio Views (`api/audio_views.py`):
   ```python
   class AudioSynthesisView(APIView):
       async def post(self, request):
           text = request.data.get('text')
           if not text:
               return Response(
                   {'error': 'Text is required'}, 
                   status=status.HTTP_400_BAD_REQUEST
               )

           try:
               audio_content = await tts_service.synthesize_speech(text)
               audio_url = save_audio_file(audio_content)
               return Response({'audio_url': audio_url})
           except Exception as e:
               return Response(
                   {'error': str(e)}, 
                   status=status.HTTP_500_INTERNAL_SERVER_ERROR
               )
   ```

3. Frontend Integration:
   ```typescript
   const playAudio = async (text: string) => {
     try {
       const { audio_url } = await audioApi.getWordAudio(text);
       const audio = new Audio(audio_url);
       await audio.play();
     } catch (error) {
       console.error('Error playing audio:', error);
     }
   };
   ```

#### Database Models
1. Word
   - urdu: TextField
   - urdlish: TextField
   - english: TextField
   - parts: TextField (word type: verb, noun, etc.)
   - example: TextField
   - etymology: TextField
   - difficulty_level: IntegerField
   - usage_frequency: IntegerField
   - created_at: DateTimeField

2. FlashcardGame
   - user: TextField
   - score: IntegerField
   - streak: IntegerField
   - max_streak: IntegerField
   - total_cards: IntegerField
   - cards_reviewed: IntegerField
   - start_time: DateTimeField
   - end_time: DateTimeField
   - completed: BooleanField

3. FlashcardReview
   - game: ForeignKey(FlashcardGame)
   - word: ForeignKey(Word)
   - confidence_level: IntegerField (0-5 scale)
   - time_spent: IntegerField (seconds)
   - created_at: DateTimeField

4. FlashcardStats
   - user: TextField (unique)
   - cards_reviewed: IntegerField
   - total_time_spent: IntegerField (minutes)
   - best_streak: IntegerField
   - last_reviewed: DateTimeField

#### API Endpoints
1. GET /api/flashcards/
   - Get next set of flashcards
   - Response:
   ```json
   {
     "id": 123,
     "user": "user123",
     "words": [
       {
         "id": 1,
         "urdu": "کتاب",
         "urdlish": "kitaab",
         "english": "book",
         "parts": "noun",
         "example": "یہ ایک اچھی کتاب ہے",
         "etymology": "From Arabic: كِتَاب"
       },
       // ... more words
     ],
     "score": 0,
     "streak": 0,
     "max_streak": 0,
     "cards_reviewed": 0,
     "total_cards": 10
   }
   ```

2. POST /api/flashcards/
   - Create new flashcard game
   - Response:
   ```json
   {
     "id": 123,
     "user": "user123",
     "words": [/* array of word objects */],
     "score": 0,
     "streak": 0,
     "max_streak": 0,
     "cards_reviewed": 0,
     "total_cards": 10,
     "start_time": "2025-04-05T17:42:57Z",
     "end_time": null,
     "completed": false
   }
   ```

3. GET /api/flashcards/stats/
   - Get user statistics
   - Response:
   ```json
   {
     "user": "user123",
     "cards_reviewed": 150,
     "total_time_spent": 45,
     "best_streak": 8,
     "last_reviewed": "2025-04-05T17:30:00Z",
     "average_time_per_card": 18
   }
   ```

4. PUT /api/flashcards/{id}/
   - Update flashcard review
   - Request:
   ```json
   {
     "word_id": 1,
     "confidence_level": 4,
     "time_spent": 15
   }
   ```
   - Response:
   ```json
   {
     "id": 123,
     "user": "user123",
     "words": [/* array of word objects */],
     "score": 5,
     "streak": 1,
     "max_streak": 3,
     "cards_reviewed": 6,
     "total_cards": 10
   }
   ```

5. POST /api/audio/synthesize/
   - Generate audio for Urdu text
   - Request:
   ```json
   {
     "text": "کتاب"
   }
   ```
   - Response:
   ```json
   {
     "audio_url": "http://localhost:8000/media/audio/temp/123abc.mp3"
   }
   ```
