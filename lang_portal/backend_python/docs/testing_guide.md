# API Testing Guide

This guide explains how to test the various endpoints in the Language Learning Portal API.

## Prerequisites

1. Install httpie for easier API testing:

```bash
pip install httpie
```

1. Start the development server:
```bash
python -m invoke runserver
```

## Testing Endpoints

### Dashboard Endpoints

1. Quick Stats
```bash
http GET http://localhost:8000/api/dashboard/quick-stats/
```
Expected response:
```json
{
    "success_rate": 80.0,
    "total_study_sessions": 4,
    "total_active_groups": 3,
    "study_streak_days": 4
}
```

2. Last Study Session
```bash
http GET http://localhost:8000/api/dashboard/last-study-session/
```
Expected response:
```json
{
    "id": 123,
    "group_id": 456,
    "created_at": "2025-02-08T17:20:23-05:00",
    "study_activity_id": 789,
    "group_name": "Basic Greetings"
}
```

3. Study Progress
```bash
http GET http://localhost:8000/api/dashboard/study-progress/
```
Expected response:
```json
{
    "total_words_studied": 3,
    "total_available_words": 124
}
```

### Word Management

1. List Words
```bash
http GET http://localhost:8000/api/words/
```

2. Get Word Details
```bash
http GET http://localhost:8000/api/words/1/
```

3. Create Word
```bash
http POST http://localhost:8000/api/words/ \
    urdu="سلام" \
    urdlish="salaam" \
    english="hello" \
    parts:='{"pos":["interjection"],"categories":["common","greetings"],"difficulty":"beginner"}'
```

### Group Management

1. List Groups
```bash
http GET http://localhost:8000/api/groups/
```

2. Get Group Details
```bash
http GET http://localhost:8000/api/groups/1/
```

3. Get Group Words
```bash
http GET http://localhost:8000/api/groups/1/words/
```

4. Create Group
```bash
http POST http://localhost:8000/api/groups/ name="Basic Phrases"
```

### Study Sessions

1. Start Study Session
```bash
http POST http://localhost:8000/api/study-activities/start_session/ \
    group_id=1 \
    study_activity_id=1
```

2. Record Word Review
```bash
http POST http://localhost:8000/api/study-sessions/1/review_word/ \
    word_id=1 \
    correct:=true
```

### System Management

1. Reset Study History
```bash
http POST http://localhost:8000/api/reset-history/
```

2. Full System Reset
```bash
http POST http://localhost:8000/api/full-reset/
```

## Testing with Sample Data

1. First, seed the database with sample data:
```bash
python -m invoke seed-all
```

2. Test a complete study flow:
```bash
# 1. Get available groups
http GET http://localhost:8000/api/groups/

# 2. Get words in a group
http GET http://localhost:8000/api/groups/1/words/

# 3. Start a study session
http POST http://localhost:8000/api/study-activities/start_session/ group_id=1 study_activity_id=1

# 4. Record some word reviews
http POST http://localhost:8000/api/study-sessions/1/review_word/ word_id=1 correct:=true
http POST http://localhost:8000/api/study-sessions/1/review_word/ word_id=2 correct:=false

# 5. Check dashboard stats
http GET http://localhost:8000/api/dashboard/quick-stats/
```

## Rate Limiting

The API includes rate limiting:
- Anonymous users: 100 requests per minute
- Study sessions: 30 requests per minute
- Word reviews: 60 requests per minute

To test rate limiting:
```bash
# Run this in a loop to trigger rate limiting
for i in {1..40}; do 
    http POST http://localhost:8000/api/study-sessions/1/review_word/ word_id=1 correct:=true
done
```

## Common Issues

1. **404 Not Found**: Check if the ID exists in the database
2. **400 Bad Request**: Verify the request payload matches the expected format
3. **429 Too Many Requests**: You've hit the rate limit, wait a minute and try again

## Using the Swagger UI

For interactive API testing:
1. Visit http://localhost:8000/swagger/
2. Click on an endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"

## Using the ReDoc Documentation

For detailed API documentation:
1. Visit http://localhost:8000/redoc/
2. Browse the organized documentation
3. Use the search function to find specific endpoints

## Monitoring

1. Check application logs:
```bash
tail -f logs/debug.log
```

2. View health status:
```bash
http GET http://localhost:8000/health/
``` 