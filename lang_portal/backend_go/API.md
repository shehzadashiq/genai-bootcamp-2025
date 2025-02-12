# API Documentation

All endpoints return JSON responses and are prefixed with `/api`.

## Dashboard

### GET /dashboard/last_study_session

Returns the most recent study session.

#### Response

```json
{
    "id": 1,
    "activity_name": "Vocabulary Quiz",
    "group_name": "Basic Words",
    "start_time": "2024-03-10T15:30:00Z",
    "end_time": "2024-03-10T15:40:00Z",
    "review_items_count": 10
}
```

### GET /dashboard/study_progress

Returns overall study progress.

#### Response

```json
{
    "total_words_studied": 50,
    "total_available_words": 100
}
```

### GET /dashboard/quick-stats

Returns dashboard statistics.

#### Response

```json
{
    "success_rate": 85.5,
    "total_study_sessions": 10,
    "total_active_groups": 3,
    "study_streak_days": 5
}
```

## Study Activities

### GET /study_activities/:id

Returns details of a specific study activity.

#### Response

```json
{
    "id": 1,
    "name": "Vocabulary Quiz",
    "thumbnail_url": "https://example.com/thumbnails/1.jpg",
    "description": "Practice your vocabulary with flashcards"
}
```

### GET /study_activities/:id/study_sessions?page=1

Returns paginated list of study sessions for an activity.

#### Response

```json
{
    "items": [
        {
            "id": 1,
            "activity_name": "Vocabulary Quiz",
            "group_name": "Basic Words",
            "start_time": "2024-03-10T15:30:00Z",
            "end_time": "2024-03-10T15:40:00Z",
            "review_items_count": 10
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 50,
        "items_per_page": 100
    }
}
```

### POST /study_activities

Creates a new study activity.

#### Request

```json
{
    "group_id": 1,
    "study_activity_id": 1
}
```

#### Response

```json
{
    "id": 2,
    "name": "Study Session 2",
    "description": "New study session"
}
```

## Words

### GET /words?page=1

Returns paginated list of words.

#### Response

```json
{
    "items": [
        {
            "urdu": "سلام",
            "urdlish": "salaam",
            "english": "hello",
            "correct_count": 5,
            "wrong_count": 1
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 50,
        "items_per_page": 100
    }
}
```

### GET /words/:id

Returns details of a specific word.

#### Response

```json
{
    "urdu": "سلام",
    "urdlish": "salaam",
    "english": "hello",
    "correct_count": 5,
    "wrong_count": 1
}
```

## Groups

### GET /groups?page=1

Returns paginated list of groups.

#### Response

```json
{
    "items": [
        {
            "id": 1,
            "name": "Basic Words",
            "word_count": 20
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 50,
        "items_per_page": 100
    }
}
```

### GET /groups/:id

Returns details of a specific group.

#### Response

```json
{
    "id": 1,
    "name": "Basic Words",
    "word_count": 20
}
```

### GET /groups/:id/words?page=1
Returns paginated list of words in a group.

#### Response

```json
{
    "items": [
        {
            "urdu": "سلام",
            "urdlish": "salaam",
            "english": "hello",
            "correct_count": 5,
            "wrong_count": 1
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 50,
        "items_per_page": 100
    }
}
```

### GET /groups/:id/study_sessions?page=1

Returns paginated list of study sessions for a group.

#### Response

```json
{
    "items": [
        {
            "id": 1,
            "activity_name": "Vocabulary Quiz",
            "group_name": "Basic Words",
            "start_time": "2024-03-10T15:30:00Z",
            "end_time": "2024-03-10T15:40:00Z",
            "review_items_count": 10
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 50,
        "items_per_page": 100
    }
}
```

## Study Sessions

### GET /study_sessions?page=1

Returns paginated list of all study sessions.

#### Response

```json
{
    "items": [
        {
            "id": 1,
            "activity_name": "Vocabulary Quiz",
            "group_name": "Basic Words",
            "start_time": "2024-03-10T15:30:00Z",
            "end_time": "2024-03-10T15:40:00Z",
            "review_items_count": 10
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 50,
        "items_per_page": 100
    }
}
```

### GET /study_sessions/:id

Returns details of a specific study session.

#### Response

```json
{
    "id": 1,
    "activity_name": "Vocabulary Quiz",
    "group_name": "Basic Words",
    "start_time": "2024-03-10T15:30:00Z",
    "end_time": "2024-03-10T15:40:00Z",
    "review_items_count": 10
}
```

### GET /study_sessions/:id/words?page=1

Returns paginated list of words reviewed in a study session.

Response:
```json
{
    "items": [
        {
            "urdu": "سلام",
            "urdlish": "salaam",
            "english": "hello",
            "correct_count": 5,
            "wrong_count": 1
        }
    ],
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 50,
        "items_per_page": 100
    }
}
```

### POST /study_sessions/:id/words/:word_id/review
Records a word review in a study session.

#### Request

```json
{
    "correct": true
}
```

#### Response

```json
{
    "word_id": 1,
    "study_session_id": 1,
    "correct": true,
    "created_at": "2024-03-10T15:35:00Z"
}
```

## System

### POST /reset_history

Resets all study history.

#### Response

```json
{
    "success": true,
    "message": "Study history has been reset"
}
```

### POST /full_reset

Resets entire system including words and groups.

#### Response

```json
{
    "success": true,
    "message": "System has been fully reset"
}
```
