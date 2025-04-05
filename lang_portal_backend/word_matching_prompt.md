# Word Matching Learning Game

## Business Goal

Create an interactive word matching game for Urdu words and their English translations that helps users learn and practice vocabulary through an engaging multiple-choice format.

Create a curated database of the top 100 most common Urdu words and their English translations using RAG technology.

## Implementation Details

### 1. Backend Structure (`word_matching/`)
- Models:
  - `WordPair`: Stores Urdu-English word pairs
  - `GameSession`: Tracks user's game progress
  - `UserProgress`: Stores historical performance

- Endpoints:
  - `POST /api/word-matching/start`: Start new game session
  - `POST /api/word-matching/submit`: Submit answer
  - `GET /api/word-matching/progress`: Get user progress
  - `GET /api/word-matching/leaderboard`: Get top scores

### 2. Vector Database Integration
- Use existing ChromaDB setup
- Collection: `word_pairs`
- Schema:
  ```python
  {
      "urdu_word": str,
      "english_translation": str,
      "difficulty_level": int,
      "usage_frequency": int,
      "embedding": List[float]  # Titan model embedding
  }
  ```

### 3. RAG Implementation
- Use AWS Bedrock for:
  - Word pair generation
  - Difficulty assessment
  - Usage frequency determination
- Validation pipeline for generated content
- Manual review option for word pairs

### 4. Game Logic
- Session flow:
  1. User starts new game
  2. System selects 10 random word pairs
  3. For each word:
     - Show Urdu word
     - Generate 4 options (1 correct, 3 distractors)
     - Track user's answer
  4. Calculate and store score
  5. Show results and correct answers

- Scoring system:
  - +10 points per correct answer
  - Streak bonuses for consecutive correct answers
  - Time-based bonus points (optional)

### 5. Frontend Integration
- New route: `/study_activities/word-matching`
- Components:
  - Game interface with multiple choice
  - Progress tracker
  - Score display
  - Results summary
  - Historical performance charts

### 6. User Progress Tracking
- Metrics stored:
  - Games played
  - Average score
  - Best score
  - Most challenging words
  - Learning progress over time

## Technical Requirements
- Utilize existing application infrastructure:
  - FastAPI backend
  - AWS Bedrock for AI/ML
  - ChromaDB for vector storage
  - AWS IAM permissions already in place

## Development Phases
1. Backend API development
2. RAG implementation for word database
3. Game logic implementation
4. Frontend development
5. Integration testing
6. User testing and feedback

## Success Metrics
- User engagement (games played)
- Learning effectiveness (score improvement)
- Word retention (repeat performance)
- User satisfaction (feedback)