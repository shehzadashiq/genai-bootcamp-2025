# Changelog

## [1.0.0] - 2025-03-09

### Added
- YouTube Integration
  - Transcript extraction with language priority
  - Video preview and metadata display
  - Support for Hindi and Urdu transcripts
  - Automatic Hindi to Urdu script conversion

- Vector Store Integration
  - ChromaDB setup with Bedrock embeddings
  - Semantic search functionality
  - Exercise storage and retrieval
  - Metadata filtering for language and user

- Question Generation
  - Bedrock-based question generator
  - Multiple choice format with explanations
  - Question validation and formatting
  - Configurable options and count

- Audio Generation
  - Amazon Polly integration
  - Hindi-Urdu script conversion
  - Fallback to gTTS when needed
  - Audio caching in session state

- Frontend UI (Streamlit)
  - Three modes: YouTube, Practice, My Exercises
  - Interactive exercise creation
  - Audio playback controls
  - Question answering interface

- Language Services
  - AWS Translate integration
  - Character mapping fallback system
  - Text normalization rules
  - Script conversion validation

### Fixed
- Transcript retrieval for auto-generated captions
- JSON parsing in question generation
- Audio generation timeout issues
- Script conversion edge cases

### Security
- Added rate limiting
- Implemented content safety checks
- Added language validation
- Added configuration validation

### Documentation
- Added comprehensive README
- Created API documentation
- Added troubleshooting guide
- Added Streamlit app guide
- Added development guide
- Added quick start guide

## [0.9.0] - 2025-03-08

### Added
- Initial project setup
- Basic AWS service integration
- Core functionality implementation
- Test environment configuration
