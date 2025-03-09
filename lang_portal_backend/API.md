# API Documentation

## Service Architecture

Our language learning platform consists of several core services that work together to provide a comprehensive learning experience:

### 1. Listening Service

#### YouTube Transcript Handling
```python
def fetch_youtube_transcript(video_id: str, language: str = 'ur') -> Dict:
```
- **Purpose**: Fetches and processes YouTube video transcripts
- **Priority Order**:
  1. Manual Hindi transcripts
  2. Auto-generated Hindi transcripts
  3. Urdu transcripts
  4. English transcripts (fallback)
- **Returns**: Dictionary with transcript segments and metadata

#### Audio Generation
```python
def generate_audio(text: str, language: str = 'ur') -> bytes:
```
- **Primary**: Amazon Polly
  - Voice: Aditi
  - Format: MP3
  - Neural TTS enabled
- **Fallback**: gTTS
  - Language mapping: ur → hi
  - Temporary file handling

### 2. Language Service

#### Script Conversion
```python
def convert_hindi_to_urdu(text: str) -> str:
```
- **Primary**: AWS Translate
  - Source: Hindi (hi)
  - Target: Urdu (ur)
  - Neural translation
- **Fallback**: Character mapping
  - Direct script conversion
  - Special case handling
  - Post-processing rules

### 3. Vector Store Service

#### Exercise Storage
```python
def store_exercise(
    text: str,
    questions: List[Dict],
    metadata: Dict,
    language: str = 'ur'
) -> str:
```
- **Backend**: ChromaDB
- **Embeddings**: Bedrock (titan-embed-text-v1)
- **Metadata**: Language, user, timestamp, source
- **Returns**: Exercise ID

#### Similarity Search
```python
def search_similar(
    query: str,
    filter_metadata: Dict = None,
    limit: int = 5
) -> List[Dict]:
```
- **Method**: Cosine similarity
- **Threshold**: 0.7 (configurable)
- **Filters**: Language, user, date range
- **Returns**: List of similar exercises

### 4. Question Generator

#### Multiple Choice Generation
```python
def generate_questions(
    text: str,
    num_questions: int = 5,
    language: str = 'ur'
) -> List[Dict]:
```
- **Backend**: Amazon Bedrock
- **Model**: Claude
- **Format**: JSON with questions, options, answers
- **Validation**: Structure, language, completeness

## API Endpoints

### 1. Exercise Creation

#### Create from YouTube
```http
POST /api/exercises/youtube
Content-Type: application/json

{
    "video_id": "string",
    "language": "ur",
    "num_questions": 5
}
```

**Response**:
```json
{
    "exercise_id": "string",
    "transcript": {
        "segments": [
            {
                "text": "string",
                "start": float,
                "duration": float
            }
        ]
    },
    "questions": [
        {
            "question": "string",
            "options": ["string"],
            "correct_answer": int,
            "explanation": "string"
        }
    ],
    "audio_url": "string"
}
```

#### Create from Text
```http
POST /api/exercises/text
Content-Type: application/json

{
    "text": "string",
    "language": "ur",
    "num_questions": 5
}
```

**Response**: Same as YouTube endpoint

### 2. Exercise Management

#### List Exercises
```http
GET /api/exercises
Query Parameters:
- language (string, optional)
- limit (integer, default: 10)
- offset (integer, default: 0)
```

**Response**:
```json
{
    "exercises": [
        {
            "id": "string",
            "text": "string",
            "language": "string",
            "created_at": "datetime",
            "question_count": int
        }
    ],
    "total": int,
    "limit": int,
    "offset": int
}
```

#### Get Exercise
```http
GET /api/exercises/{exercise_id}
```

**Response**:
```json
{
    "id": "string",
    "text": "string",
    "language": "string",
    "questions": [
        {
            "question": "string",
            "options": ["string"],
            "correct_answer": int,
            "explanation": "string"
        }
    ],
    "audio_url": "string",
    "created_at": "datetime",
    "metadata": {
        "source": "string",
        "video_id": "string",
        "user_id": "string"
    }
}
```

### 3. Language Services

#### Convert Script
```http
POST /api/language/convert
Content-Type: application/json

{
    "text": "string",
    "source": "hi",
    "target": "ur"
}
```

**Response**:
```json
{
    "converted_text": "string",
    "method_used": "string"  // "aws" or "mapping"
}
```

#### Generate Audio
```http
POST /api/language/audio
Content-Type: application/json

{
    "text": "string",
    "language": "ur"
}
```

**Response**:
```json
{
    "audio_url": "string",
    "duration": float,
    "service_used": "string"  // "polly" or "gtts"
}
```

### 4. Search

#### Similar Exercises
```http
POST /api/search/similar
Content-Type: application/json

{
    "query": "string",
    "language": "ur",
    "limit": 5,
    "min_similarity": 0.7
}
```

**Response**:
```json
{
    "results": [
        {
            "exercise_id": "string",
            "text": "string",
            "similarity": float,
            "metadata": object
        }
    ]
}
```

## Error Handling

All endpoints follow this error response format:

```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": object
    }
}
```

Common error codes:
- `TRANSCRIPT_NOT_FOUND`: No suitable transcript available
- `CONVERSION_FAILED`: Script conversion failed
- `GENERATION_FAILED`: Question/audio generation failed
- `INVALID_REQUEST`: Invalid request parameters
- `SERVICE_ERROR`: Internal service error

## Rate Limiting

- Default: 100 requests per minute
- Audio generation: 20 requests per minute
- Question generation: 10 requests per minute
- Search: 50 requests per minute

## Authentication

Bearer token authentication required for all endpoints:

```http
Authorization: Bearer <token>
```

## Websocket Events

### Exercise Progress
```javascript
// Connect to websocket
ws://api/ws/exercises/{exercise_id}

// Events
{
    "type": "transcript_progress",
    "data": {
        "status": "string",
        "progress": float,
        "current_segment": int
    }
}

{
    "type": "question_progress",
    "data": {
        "status": "string",
        "questions_generated": int,
        "total_questions": int
    }
}
```

## Development Guidelines

1. **Error Handling**
   - Use appropriate HTTP status codes
   - Include detailed error messages
   - Log errors with stack traces

2. **Response Format**
   - Use consistent JSON structure
   - Include pagination where applicable
   - Follow REST conventions

3. **Security**
   - Validate all inputs
   - Sanitize text content
   - Rate limit by IP and token

4. **Performance**
   - Cache frequent responses
   - Use async operations
   - Batch database queries
