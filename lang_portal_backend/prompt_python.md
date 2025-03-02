# Backend Server Technical Specs

## Business Goal

A language learning school wants to build a prototype of learning portal which will act as three things:

- Inventory of possible vocabulary that can be learned
- Act as a Learning record store (LRS), providing correct and wrong score on practice vocabulary
- A unified launchpad to launch different learning apps

## Technical Requirements

- The backend will be built using Python
- The database will be SQLite3
- The API will be built using Django
- Invoke is a task runner for Python
- The API will always return JSON
- There will no authentication or authorization
- Everything will be treated as a single user
- The application should run on port `8080`

## Directory Structure

```text
backend_python/
├── cmd/
│   └── server/        # Entry point for starting the server
├── internal/
│   ├── models/        # Data structures and database operations (SQLAlchemy, Pydantic, etc.)
│   ├── handlers/      # HTTP handlers (Django, FastAPI, Flask views, etc.), organized by feature
│   └── service/       # Business logic
├── db/
│   ├── migrations/    # Database migrations (Alembic, Django migrations, etc.)
│   └── seeds/         # For initial data population
├── scripts/           # Equivalent of magefile.go, for automation tasks (invoke, Makefile, etc.)
│   ├── manage.py      # CLI tool for running tasks
├── requirements.txt   # Dependencies for the project
├── pyproject.toml     # Modern Python project configuration
└── words.db           # SQLite database
```

## Database Schema

Our database will be a single sqlite database called `words.db` that will be in the root of the project folder of `lang_portal_backend`

We have the following tables:

- words - stored vocabulary words
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - urdu TEXT NOT NULL
  - urdlish TEXT NOT NULL
  - english TEXT NOT NULL
  - parts TEXT
  - created_at DATETIME DEFAULT CURRENT_TIMESTAMP
- groups - thematic groups of words
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - name TEXT NOT NULL UNIQUE
  - word_count INTEGER NOT NULL DEFAULT 0
  - created_at DATETIME DEFAULT CURRENT_TIMESTAMP
- words_groups - join table for words and groups many-to-many
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - word_id INTEGER NOT NULL
  - group_id INTEGER NOT NULL
  - FOREIGN KEY (word_id) REFERENCES words(id)
  - FOREIGN KEY (group_id) REFERENCES groups(id)
- study_activities - a specific study activity type (e.g., Vocabulary Quiz)
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - name TEXT NOT NULL UNIQUE
  - url TEXT
  - thumbnail_url TEXT
  - description TEXT
  - created_at DATETIME DEFAULT CURRENT_TIMESTAMP
- study_sessions - records of study sessions
  - id INTEGER PRIMARY KEY AUTOINCREMENT
  - group_id INTEGER NOT NULL
  - study_activity_id INTEGER NOT NULL
  - created_at DATETIME NOT NULL
  - FOREIGN KEY (group_id) REFERENCES groups(id)
  - FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
- word_review_items - a record of word practice
  - word_id INTEGER NOT NULL
  - study_session_id INTEGER NOT NULL
  - correct BOOLEAN NOT NULL
  - created_at DATETIME NOT NULL
  - FOREIGN KEY (word_id) REFERENCES words(id)
  - FOREIGN KEY (study_session_id) REFERENCES study_sessions(id)
  - UNIQUE(study_session_id, word_id)

## API Endpoints

### GET /api/dashboard/last_study_session

Returns information about the most recent study session.

#### JSON Response

```json
{
  "id": 123,
  "group_id": 456,
  "activity_name": "Vocabulary Quiz",
  "group_name": "Basic Greetings",
  "start_time": "2025-02-08T17:20:23-05:00",
  "end_time": "2025-02-08T17:30:23-05:00",
  "review_items_count": 20
}
```

### GET /api/dashboard/study_progress

Returns study progress statistics.

#### JSON Response

```json
{
  "total_words_studied": 3,
  "total_available_words": 124
}
```

### GET /api/dashboard/quick-stats

Returns quick overview statistics.

#### JSON Response

```json
{
  "success_rate": 80.0,
  "total_words_studied": 50,
  "correct_count": 40,
  "correct_percentage": 80,
  "total_available_words": 124,
  "total_study_sessions": 4,
  "total_active_groups": 3,
  "study_streak_days": 4
}
```

### GET /api/study_activities/:id

#### JSON Response

```json
{
  "id": 1,
  "name": "Vocabulary Quiz",
  "url": "The full URL of the study activity",
  "thumbnail_url": "/images/thumbnails/vocabulary.svg",
  "description": "Practice your vocabulary with flashcards",
  "created_at": "2025-02-08T17:20:23-05:00"
}
```

### GET /api/study_activities/:id/study_sessions

Returns paginated list of study sessions for a specific activity.

#### Query Parameters

- page (optional): Page number for pagination (default: 1)
- per_page (optional): Items per page (default: 100)

#### JSON Response

```json
{
  "items": [
    {
      "id": 123,
      "group_id": 456,
      "activity_name": "Vocabulary Quiz",
      "group_name": "Basic Greetings",
      "start_time": "2025-02-08T17:20:23-05:00",
      "end_time": "2025-02-08T17:30:23-05:00",
      "review_items_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 20
  }
}
```

### POST /api/study_activities

Creates a new study activity.

#### Request Body

```json
{
  "group_id": 123,
  "activity_id": 456
}
```

#### JSON Response

```json
{
  "id": 1,
  "name": "Vocabulary Quiz",
  "url": "The full URL of the study activity",
  "thumbnail_url": "/images/thumbnails/vocabulary.svg",
  "description": "Practice your vocabulary with flashcards",
  "created_at": "2025-02-08T17:20:23-05:00"
}
```

### POST /api/study_sessions

Creates a new study session.

#### Request Body

```json
{
  "group_id": 123,
  "study_activity_id": 456
}
```

#### JSON Response

```json
{
  "id": 124,
  "group_id": 123,
  "activity_name": "Vocabulary Quiz",
  "group_name": "Basic Greetings",
  "start_time": "2025-02-08T17:20:23-05:00",
  "end_time": "2025-02-08T17:30:23-05:00",
  "review_items_count": 0
}
```

### GET /api/words

Returns a paginated list of words.

#### Query Parameters

- page (optional): Page number for pagination (default: 1)
- per_page (optional): Items per page (default: 100)

#### JSON Response

```json
{
  "items": [
    {
      "id": 1,
      "urdu": "سلام",
      "urdlish": "salaam",
      "english": "hello",
      "correct_count": 5,
      "wrong_count": 2
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 500,
    "items_per_page": 100
  }
}
```

### GET /api/study_sessions/:id

Returns details of a specific study session.

#### JSON Response

```json
{
  "id": 123,
  "group_id": 456,
  "activity_name": "Vocabulary Quiz",
  "group_name": "Basic Greetings",
  "start_time": "2025-02-08T17:20:23-05:00",
  "end_time": "2025-02-08T17:30:23-05:00",
  "review_items_count": 20
}
```

### GET /api/study_sessions/:id/words

Returns a paginated list of words reviewed in a specific study session.

#### Query Parameters

- page (optional): Page number for pagination (default: 1)
- per_page (optional): Items per page (default: 100)

#### JSON Response

```json
{
  "items": [
    {
      "id": 1,
      "urdu": "سلام",
      "urdlish": "salaam",
      "english": "hello",
      "correct_count": 5,
      "wrong_count": 2
      "created_at": "2025-02-08T17:20:23-05:00"
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 5,
    "total_items": 100,
    "items_per_page": 20
  }
}
```

### POST /api/study_sessions/:id/words/:word_id/review

Records a word review for a study session.

#### Request Body

```json
{
  "correct": true
}
```

#### JSON Response

```json
{
  "id": 1,
  "word_id": 123,
  "study_session_id": 456,
  "correct": true,
  "created_at": "2025-02-08T17:20:23-05:00"
}
```

### POST /api/groups/:id/words

Adds words to a group.

#### Request Body

```json
{
  "word_ids": [1, 2, 3]
}
```

#### JSON Response

```json
{
  "id": 123,
  "name": "Basic Greetings",
  "word_count": 3
}
```

## Task Runner Tasks

The project uses Mage as a task runner. Here are the key tasks available:

### Initialize Database

This task will initialize a new SQLite database called `words.db` in WAL mode with foreign key constraints enabled:

```bash
mage initdb
mage migrate
mage seed
```

### Migrate Database

This task will run all SQL migration files from the `db/migrations` folder in alphabetical order:

```bash
mage migrate
```

Migration files should follow this naming pattern:
```
0001_init.sql
0002_add_new_table.sql
...
```

### Seed Data

This task will import json files and transform them into target data for our database.

All seed files are in the `db/seeds` folder.


```bash
mage seed
```

The seed files should contain word data in this format:

```json
[
  {
    "urdu": "ادائیگی",
    "urdlish": "adaegee",
    "english": "pay",
    "parts": {}
  }
]
```

Each seed file will be associated with a word group during import.

## Error Handling

All API endpoints follow a consistent error response format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "word_count",
      "reason": "must be between 1 and 50"
    }
  }
}
```

Common error codes:

- `VALIDATION_ERROR` - Invalid input parameters
- `NOT_FOUND` - Requested resource not found
- `INTERNAL_ERROR` - Internal server error
- `CONFLICT` - Resource conflict (e.g., duplicate entry)
- `BAD_REQUEST` - Malformed request
