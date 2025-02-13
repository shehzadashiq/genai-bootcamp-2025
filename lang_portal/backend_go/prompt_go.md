# Backend Server Technical Specs

## Business Goal

A language learning school wants to build a prototype of learning portal which will act as three things

- Inventory of possible vocabulary that can be learned
- Act as a  Learning record store (LRS), providing correct and wrong score on practice vocabulary
- A unified launchpad to launch different learning apps

## Technical Requirements

- The backend will be built using Go
- The database will be SQLite3
- The API will be built using Gin
- Mage is a task runner for Go.
- The API will always return JSON
- There will no authentication or authorization
- Everything be treated as a single user

## Directory Structure

```text
backend_go/
├── cmd/
│   └── server/
├── internal/
│   ├── models/     # Data structures and database operations
│   ├── handlers/   # HTTP handlers organized by feature (dashboard, words, groups, etc.)
│   └── service/    # Business logic
├── db/
│   ├── migrations/
│   └── seeds/      # For initial data population
├── magefile.go
├── go.mod
└── words.db
```

## Database Schema

Our database will be a single sqlite database called `words.db` that will be in the root of the project folder of `backend_go`

We have the following tables

- words - stored vocabulary words
  - id integer
  - urdu string
  - urdlish string
  - english string
  - parts json
- words_groups - join table for words and groups many-to-many
  - id integer
  - word_id integer
  - group_id integer
- groups - thematic groups of words
  - id integer
  - name string
- study_sessions - records of study sessions grouping word_review_items
  - id integer
  - group_id integer
  - created_at datetime
  - study_activity_id integer
- study_activities - a specific study activity type (e.g., Vocabulary Quiz), linking a study session to group
  - id integer
  - name string
  - url string
  - thumbnail_url string
  - description string
  - created_at datetime
- word_review_items - a record of word practice, determining if the word was correct or not
  - word_id integer
  - study_session_id integer
  - correct boolean
  - created_at datetime

## API Endpoints

### GET /api/dashboard/last_study_session

Returns information about the most recent study session.

#### JSON Response

```json
{
  "id": 123,
  "activity_name": "Vocabulary Quiz",
  "group_name": "Basic Greetings",
  "start_time": "2025-02-08T17:20:23-05:00",
  "end_time": "2025-02-08T17:30:23-05:00",
  "review_items_count": 20
}
```

### GET /api/dashboard/study_progress

Returns study progress statistics.
Please note that the frontend will determine progress bar based on total words studied and total available words.

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
  "thumbnail_url": "https://example.com/thumbnail.jpg",
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

Creates a new study session for an activity.

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

### POST /api/study_sessions/:id/words/:word_id/review

Records a word review result for a study session.

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

## Task Runner Tasks

Lets list out possible tasks we need for our lang portal.

### Initialize Database

This task will initialize the sqlite database called `words.db

### Migrate Database

This task will run a series of migrations sql files on the database

Migrations live in the `migrations` folder.
The migration files will be run in order of their file name.
The file names should looks like this:

```sql
0001_init.sql
0002_create_words_table.sql
```

### Seed Data

This task will import json files and transform them into target data for our database.

All seed files live in the `seeds` folder.

In our task we should have DSL to specific each seed file and its expected group word name.

```json
[
  {
    "urdu": "ادائیگی",
    "urdlish": "adaegee",
    "english": "pay",
  },
  ...
]
```
