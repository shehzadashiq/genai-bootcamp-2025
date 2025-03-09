# Language Learning Portal Backend

A Django-based backend service for the Language Learning Portal, providing RESTful APIs for vocabulary management, study sessions, and progress tracking.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- SQLite3
- pip (Python package manager)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd lang_portal_backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python manage.py migrate
   ```

5. Load seed data:
   ```bash
   python manage.py loaddata db/seeds/*.json
   ```

### Running the Server

Start the development server:
```bash
python manage.py runserver 8080
```

The API will be available at `http://localhost:8080/api`

## API Endpoints

### Dashboard
- `GET /api/dashboard/last_study_session/` - Get the most recent study session
- `GET /api/dashboard/study_progress/` - Get study progress statistics
- `GET /api/dashboard/quick-stats/` - Get quick statistics overview

### Study Activities
- `GET /api/study_activities/` - List all study activities
- `GET /api/study_activities/<id>/` - Get specific study activity
- `GET /api/study_activities/<id>/study_sessions/` - Get sessions for an activity
- `POST /api/study_activities/` - Create a new study session

### Words
- `GET /api/words/` - List all words (paginated)
- `GET /api/words/<id>/` - Get specific word details
- `POST /api/study_sessions/<session_id>/words/<word_id>/review` - Submit word review

### Groups
- `GET /api/groups/` - List all word groups
- `GET /api/groups/<id>/` - Get specific group details
- `GET /api/groups/<id>/words/` - Get words in a group

### Listening Practice
- `POST /api/listening/questions` - Generate questions from a YouTube video
  - Request body: `{ "url": "youtube_video_url" }`
  - Response: List of questions with options and correct answers
- `POST /api/listening/test-hindi-to-urdu` - Convert Hindi text to Urdu script
  - Request body: `{ "text": "hindi_text" }`
  - Response: `{ "urdu_text": "converted_text" }`

## Listening Practice Feature

### Overview
The listening practice feature allows users to practice listening comprehension using YouTube videos. The system generates questions based on the video content and provides immediate feedback.

### Features
- YouTube video integration
- Automatic question generation
- Interactive quiz interface
- Immediate feedback and scoring
- Progress tracking
- Hindi to Urdu script conversion support

### Translation System

The Hindi to Urdu translation system uses a dual-approach strategy:

1. Primary Method: AWS Translate
   - Uses AWS Translate service for accurate translations
   - Handles complex grammar and idioms
   - Maintains proper word order
   - Converts numerals appropriately
   - Preserves punctuation

2. Fallback Method: Character Mapping
   - Direct character-to-character mapping
   - Handles special cases and combined characters
   - Post-processing for common issues

3. Text Normalization
   - Proper word spacing
   - Character combinations
   - Arabic/Persian to Urdu character normalization

### AWS Configuration

Required AWS IAM permissions:
- `translate:TranslateText`
- `bedrock:InvokeModel`

Recommended policy name: "TranslateAndBedrockAccess"

### Frontend Components

The listening practice interface includes:
1. Video URL input
2. Question display with multiple choice options
3. Navigation between questions
4. Submit functionality on the last question
5. Results view showing:
   - Total score
   - Individual question review
   - Correct/incorrect answer highlighting
   - Option to try again

### Error Handling

The system includes comprehensive error handling for:
1. Invalid YouTube URLs
2. Translation service failures
3. Network connectivity issues
4. Invalid input text formats

### Dependencies

Added dependencies:
- boto3 (1.34.34)
- botocore (1.34.34)
- python-dotenv (1.0.1)

### Environment Variables

Required environment variables:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
```

### Troubleshooting Translation Issues

1. **AWS Translation Service Issues**
   - Verify AWS credentials are correct
   - Check AWS service quotas
   - Ensure proper IAM permissions
   - Monitor AWS service health

2. **Character Mapping Issues**
   - Check input text encoding
   - Verify character combinations
   - Review normalization rules
   - Monitor post-processing results

3. **Performance Optimization**
   - Cache frequent translations
   - Monitor API usage
   - Implement rate limiting
   - Use batch processing for multiple translations

## Project Structure

```text
lang_portal_backend/
├── api/                    # API app directory
│   ├── views.py           # API view definitions
│   ├── serializers.py     # DRF serializers
│   ├── urls.py            # API URL routing
│   └── models.py          # Database models
├── db/                    # Database related files
│   └── seeds/            # Seed data JSON files
├── lang_portal/          # Project settings directory
│   ├── settings.py      # Django settings
│   ├── urls.py         # Project URL routing
│   └── wsgi.py        # WSGI configuration
├── requirements.txt    # Python dependencies
└── manage.py         # Django management script
```

## Troubleshooting

### Common Issues and Solutions

1. **Database Migration Issues**
   - Error: "No such table" or "table already exists"
   - Solutions:
     - Delete the `db.sqlite3` file and run migrations again
     - Run `python manage.py migrate --run-syncdb`
     - Check migration files in each app's migrations folder
     - Try `python manage.py showmigrations` to see migration status

2. **Seed Data Loading Errors**
   - Error: "Invalid JSON" or "No such table"
   - Solutions:
     - Verify JSON files are properly formatted
     - Ensure migrations are run before loading data
     - Check file permissions on seed files
     - Try loading seed files one at a time to isolate issues

3. **Server Start Issues**
   - Error: "Port 8080 already in use"
   - Solutions:
     - Kill the process using port 8080
     - Use a different port: `python manage.py runserver 8081`
     - Check for other Django instances running
     - Restart your development machine

4. **CORS Issues**
   - Error: "CORS policy" errors in frontend console
   - Solutions:
     - Check `CORS_ALLOWED_ORIGINS` in settings.py
     - Verify frontend origin matches allowed origins
     - Try adding frontend origin to `CORS_ALLOWED_ORIGINS`
     - Enable CORS debug logging in settings.py

### Debugging Tips

1. **Enable Debug Logging**
   Add to settings.py:
   ```python
   LOGGING = {
       'version': 1,
       'disable_existing_loggers': False,
       'handlers': {
           'console': {
               'class': 'logging.StreamHandler',
           },
       },
       'root': {
           'handlers': ['console'],
           'level': 'DEBUG',
       },
   }
   ```

2. **Database Debugging**
   - Use Django shell: `python manage.py shell`
   - Check model queries: `Model.objects.all().query`
   - Use `django-debug-toolbar` for SQL analysis
   - Monitor database connections and query performance

3. **API Endpoint Testing**
   - Use Django REST framework browsable API
   - Test with curl or Postman
   - Check request/response headers
   - Verify payload formats

4. **Performance Issues**
   - Use Django Debug Toolbar
   - Check for N+1 query problems
   - Monitor memory usage
   - Profile slow endpoints

### Getting Help

If you're still experiencing issues:

1. Check Django documentation
2. Search Stack Overflow with the error message
3. Create a new issue with:
   - Python and Django versions
   - Full error traceback
   - Steps to reproduce
   - Relevant code snippets
   - Database schema if relevant

## Development Guidelines

1. Follow PEP 8 style guide
2. Write tests for new features
3. Update documentation when making changes
4. Use meaningful commit messages

# Language Learning Portal

A comprehensive language learning platform with a focus on Urdu listening comprehension, powered by AWS services and Streamlit.

## Features

### Core Components
1. **YouTube Integration**
   - Transcript extraction using youtube-transcript-api
   - Video preview and metadata display
   - Support for Hindi and Urdu transcripts
   - Automatic Hindi to Urdu script conversion

2. **Vector Store Integration**
   - ChromaDB for exercise storage
   - Bedrock embeddings for semantic search
   - Metadata filtering by language and user
   - CRUD operations for exercises

3. **Question Generation**
   - Bedrock-based question generator
   - Multiple choice format with explanations
   - Configurable number of questions and options
   - Question validation and formatting

4. **Audio Generation**
   - Amazon Polly integration for TTS
   - Hindi-Urdu script conversion
   - Fallback character mapping system
   - Audio caching in session state

## Getting Started

### Prerequisites
- Python 3.8+
- AWS Account with access to:
  - Amazon Bedrock
  - Amazon Polly
  - Amazon Translate

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd lang_portal_backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure AWS credentials:
Create a `.env` file with:
```
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=your_region
```

### Running the Application

Start the Streamlit app:
```bash
streamlit run listening_app.py
```

The app will be available at `http://localhost:8501`

## Usage Guide

### 1. YouTube Exercise Mode
- Enter a YouTube video ID
- System will:
  1. Extract transcript (prioritizes Hindi, falls back to Urdu/English)
  2. Convert Hindi script to Urdu if needed
  3. Generate multiple-choice questions
  4. Create audio using TTS

### 2. Practice Mode
- Enter custom text
- System generates:
  1. Multiple-choice questions
  2. Audio playback
  3. Interactive exercise interface

### 3. My Exercises
- View saved exercises
- Search by similarity
- Track progress

## Architecture

### 1. Transcript Handling
```python
# Priority order:
1. Manual Hindi transcript
2. Auto-generated Hindi transcript
3. Urdu transcript
4. English transcript (fallback)
```

### 2. Script Conversion
```python
# Two-tier approach:
1. AWS Translate (hi → ur)
2. Fallback: Character mapping system
```

### 3. Vector Store
```python
# ChromaDB configuration:
- Collection name: "exercises"
- Embedding: Bedrock (titan-embed-text-v1)
- Persistence: Local directory
```

## Troubleshooting

### 1. Transcript Issues
- **No transcript found**
  - Check video ID is correct
  - Verify video has captions enabled
  - Try a different language option

- **Hindi to Urdu conversion fails**
  - Check AWS credentials
  - Verify AWS Translate quota
  - System will use character mapping fallback

### 2. Audio Generation
- **Polly fails**
  - Check AWS credentials
  - Verify supported text length
  - System will use gTTS fallback

### 3. Question Generation
- **JSON parsing error**
  - Check text length is within limits
  - Verify Bedrock model availability
  - Review text for unsupported characters

### 4. Vector Store
- **ChromaDB errors**
  - Check persistence directory permissions
  - Verify embedding function is working
  - Ensure sufficient disk space

## Configuration

### 1. AWS Services
```python
# Required permissions:
- bedrock:InvokeModel
- translate:TranslateText
- polly:SynthesizeSpeech
```

### 2. Application Settings
```python
# config.py
QUESTIONS_PER_EXERCISE = 5
OPTIONS_PER_QUESTION = 4
TRANSLATION_FALLBACK = True
POLLY_VOICE_ID = "Aditi"
```

### 3. Vector Store Settings
```python
# vector_store_config.py
COLLECTION_NAME = "exercises"
PERSIST_DIRECTORY = "./chroma_db"
SIMILARITY_THRESHOLD = 0.7
```

## Project Structure
```
lang_portal_backend/
├── services/
│   ├── listening_service.py    # YouTube & transcript handling
│   ├── language_service.py     # Script conversion
│   └── vector_store_service.py # ChromaDB integration
├── config.py                   # Configuration settings
├── listening_app.py            # Streamlit application
├── question_generator.py       # Bedrock integration
├── vector_store.py            # Vector store setup
└── requirements.txt           # Dependencies
```

## Dependencies
```
# Core
streamlit>=1.24.0
chromadb>=0.4.0
langchain>=0.0.300
youtube-transcript-api>=0.6.1

# AWS
boto3>=1.34.0
botocore>=1.34.0

# Audio
gTTS>=2.3.2

# Utils
python-dotenv>=1.0.0
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License
