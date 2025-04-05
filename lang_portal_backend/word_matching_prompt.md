# Word Matching Learning Game

## Business Goal

Create an interactive word matching game for Urdu words and their English translations that helps users learn and practice vocabulary through an engaging multiple-choice format.

## Implementation Details

### 1. Backend Structure

- Models:
  - `WordMatchingGame`: Tracks game sessions and overall progress
  - `WordMatchingQuestion`: Individual questions within a game
  - `WordMatchingStats`: User statistics across all games

- API Endpoints:

#### Start Game

```http
POST /api/word-matching/start_game/
Request:
{
    "user": "string",
    "num_questions": 10
}

Response:
{
    "id": 123,
    "user": "string",
    "score": 0,
    "max_streak": 0,
    "total_questions": 10,
    "correct_answers": 0,
    "start_time": "2025-04-05T10:00:00Z",
    "end_time": null,
    "completed": false,
    "questions": [
        {
            "id": 456,
            "word_urdu": "روکنا",
            "word_urdlish": "rukna",
            "word_english": "to stop",
            "selected_answer": null,
            "is_correct": null,
            "response_time": null
        },
        // ... more questions
    ]
}
```

#### Submit Answer

```http
POST /api/word-matching/{game_id}/submit_answer/
Request:
{
    "question_id": 456,
    "answer": "to stop",
    "response_time": 2.5
}

Response:
{
    "id": 123,
    "user": "string",
    "score": 10,
    "max_streak": 1,
    "total_questions": 10,
    "correct_answers": 1,
    "start_time": "2025-04-05T10:00:00Z",
    "end_time": null,
    "completed": false,
    "questions": [
        {
            "id": 456,
            "word_urdu": "روکنا",
            "word_urdlish": "rukna",
            "word_english": "to stop",
            "selected_answer": "to stop",
            "is_correct": true,
            "response_time": 2.5
        },
        // ... more questions
    ]
}
```

#### Get Options

```http
GET /api/word-matching/{game_id}/get_options/?question_id={question_id}
Response:
{
    "options": [
        "to stop",
        "to go",
        "to run",
        "to walk"
    ]
}
```

#### Get User Stats

```http
GET /api/word-matching-stats/?user={username}
Response:
{
    "user": "string",
    "games_played": 5,
    "total_score": 150,
    "best_score": 90,
    "total_correct": 15,
    "total_questions": 20,
    "last_played": "2025-04-05T10:30:00Z",
    "accuracy": 75.0,
    "average_score": 30.0
}
```

### 2. Features

- Multiple choice format with 4 options per question
- Transliteration support (can be toggled for each word)
- Score tracking and statistics
- Immediate feedback on answers
- End-of-game review with correct/incorrect answers
- User progress tracking

### 3. Game Logic

- Session flow:
  1. User starts new game (default 10 questions)
  2. For each question:
     - Show Urdu word with optional transliteration
     - Present 4 multiple choice options
     - Track answer and response time
     - Show immediate feedback
  3. After last question:
     - Show final score and statistics
     - Display review of all questions with correct answers
     - Update user's overall statistics

- Scoring system:
  - +10 points per correct answer
  - Statistics tracked:
    - Games played
    - Total score
    - Best score
    - Accuracy percentage
    - Average score

### 4. Frontend Integration

- Route: `/study_activities/word-matching`
- Components:
  - Game interface with multiple choice
  - Progress tracker
  - Score display
  - Results summary
  - Historical performance charts
- Features:
  - Clean, centered layout
  - Large, clear Urdu text display
  - Optional transliteration toggle
  - Responsive multiple choice buttons
  - Visual feedback for correct/incorrect answers
  - Comprehensive end-game review
  - Statistics display

### 5. User Progress Tracking

- Metrics stored:
  - Games played
  - Total score
  - Best score
  - Accuracy percentage
  - Average score per game
  - Response times
  - Last played timestamp
  - Learning progress over time
- Analytics features:
  - Performance trends
  - Most challenging words
  - Session history
  - Achievement tracking

### 6. Technical Requirements

- Backend:
  - Django REST Framework for API endpoints
  - SQLite database for development
  - Django ORM for database operations
  - Django session authentication

- Frontend:
  - React with TypeScript
  - TailwindCSS for styling
  - React hooks for state management
  - Fetch API for backend communication

- Development:
  - Python virtual environment
  - Node.js and npm
  - Local development server

## Success Metrics

- User engagement (games played)
- Learning effectiveness (score improvement)
- Word retention (repeat performance)
- User satisfaction (feedback)