# Document Summarization Service

A multilingual document summarization service that extracts content from web pages, generates summaries in English and Urdu, and provides text-to-speech capabilities for both languages.

## Features

- 🌐 Web Content Extraction
- 📝 AI-Powered Text Summarization
- 🔄 English to Urdu Translation
- 🗣️ Text-to-Speech Support
  - English voice (Joanna)
  - Hindi voice (Aditi) for Urdu text
- 💾 Vector-based Caching System
- 🎯 Accurate Urdu Pronunciation
- 🚀 Docker Containerization

## OPEA Services Integration

This service integrates with several OPEA (Open Platform for Education & Assessment) services:

### Core Services
- **OPEA Translation API**
  - Used for high-quality English to Urdu translation
  - Handles complex sentence structures and idiomatic expressions
  - Maintains cultural context in translations

- **OPEA Vector Store**
  - Provides efficient caching of summaries
  - Semantic similarity search for related content
  - Built on ChromaDB with Bedrock embeddings

### Supporting Services
- **OPEA Script Converter**
  - Converts Urdu text to Devanagari script
  - Preserves pronunciation accuracy
  - Handles special character combinations

- **OPEA Audio Cache**
  - Manages generated audio files
  - Implements efficient cleanup strategies
  - Shared volume support for microservices

## Prerequisites

- Docker and Docker Compose
- AWS Account with the following services:
  - Amazon Polly
  - Amazon Bedrock
  - Amazon Translate

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1  # or your preferred region
```

## Quick Start

1. Clone the repository:
```bash
git clone <repository-url>
cd opea-comps/docsum_service
```

2. Create and configure the `.env` file with your AWS credentials

3. Build and run the services:
```bash
docker-compose up --build
```

4. Access the application:
   - Frontend: http://localhost:8501
   - API: http://localhost:8002

## Architecture

### Components

1. **Frontend (Streamlit)**
   - User interface for URL input
   - Display of summaries in both languages
   - Audio playback interface

2. **Backend (FastAPI)**
   - RESTful API endpoints
   - Service orchestration
   - Error handling and logging

3. **Services**
   - `Summarizer`: Extracts and summarizes web content
   - `Translator`: Handles English to Urdu translation
   - `TextToSpeechService`: Manages audio generation
   - `VectorStore`: Handles caching using ChromaDB

### API Endpoints

- `GET /health`: Health check endpoint
- `POST /summarize`: Main endpoint for summarization
  ```json
  {
    "url": "https://example.com",
    "use_cache": true
  }
  ```

## Development

### Project Structure

```
docsum_service/
├── app/
│   ├── main.py
│   └── services/
│       ├── summarizer.py
│       ├── translator.py
│       ├── tts.py
│       ├── script_converter.py
│       └── vectorstore.py
├── frontend/
│   └── streamlit_app.py
├── docker-compose.yml
├── Dockerfile
└── README.md
```

### Adding New Features

1. **New Language Support**
   - Add translation service in `translator.py`
   - Update TTS service with appropriate voice
   - Modify frontend to display new language

2. **Custom Voice Settings**
   - Adjust SSML parameters in `tts.py`
   - Modify prosody settings for each language

## Troubleshooting

1. **Audio Not Playing**
   - Ensure AWS credentials are correct
   - Check audio file permissions in shared volume
   - Verify browser audio support

2. **Summarization Issues**
   - Check URL accessibility
   - Verify content extraction
   - Review cache settings

3. **Translation Problems**
   - Confirm AWS Translate access
   - Check language codes
   - Verify character encoding

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request


## Acknowledgments

- AWS Services (Polly, Bedrock, Translate)
- Streamlit for the frontend framework
- FastAPI for the backend
- ChromaDB for vector storage
