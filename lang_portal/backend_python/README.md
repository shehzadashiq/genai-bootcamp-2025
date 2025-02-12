# Language Learning Portal Backend

A Django-based backend for the language learning portal.

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python -m invoke init-db
python -m invoke migrate
```

4. Seed initial data:
```bash
python -m invoke seed-all
```

## Development

### Available Commands

Use invoke to run common development tasks:

```bash
# Run database migrations
python -m invoke migrate

# Start development server
python -m invoke runserver

# Format code using black
python -m invoke format

# Run linting checks
python -m invoke lint

# Run tests
python -m invoke test

# Clean Python cache files
python -m invoke clean

# Reset database
python -m invoke reset-db

# Generate API documentation
python -m invoke generate-docs

# Seed all predefined data
python -m invoke seed-all

# Seed specific data file
python -m invoke seed-data --file-path=db/seeds/basic_words.json --group-name="Basic Words"
```

### Seeding Data

The project includes commands for seeding initial data. Seed files should be JSON files in the `db/seeds` directory with this structure:
```json
[
    {
        "urdu": "سلام",
        "urdlish": "salaam",
        "english": "hello",
        "parts": {
            "pos": [
                "interjection"
            ],
            "categories": [
                "common",
                "greetings"
            ],
            "difficulty": "beginner"
        }
    }
]
```

### Project Structure

```
backend_python/
├── config/                 # Django settings and configuration
├── internal/              # Main application code
│   ├── handlers/          # API views and request handling
│   ├── models/           # Database models and serializers
│   ├── utils/            # Utility functions and classes
│   └── management/       # Custom Django management commands
├── scripts/              # Management scripts
├── db/                   # Database and seed files
│   └── seeds/           # JSON seed data files
└── logs/                # Application logs
```

### API Documentation

After starting the development server, visit:
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## Testing

Run the test suite:
```bash
python -m invoke test
```

## Contributing

1. Format code before committing:
```bash
python -m invoke format
```

2. Run linting checks:
```bash
python -m invoke lint
```

3. Ensure all tests pass:
```bash
python -m invoke test
```

## Features

- Vocabulary management with support for Urdu, Urdlish, and English
- Study session tracking
- Progress monitoring
- Group-based vocabulary organization
- Caching for improved performance
- API rate limiting
- Comprehensive logging
- Health monitoring

## Prerequisites

- Python 3.11+
- Redis (for production caching)
- Docker and Docker Compose (for containerized deployment)

## Setup

### Local Development

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database:
```bash
python scripts/manage.py migrate
python -m invoke init-db
python -m invoke migrate
```

4. Seed initial data:
```bash
python -m invoke seed-all
```

5. Run the development server:
```bash
python scripts/manage.py runserver
```

### Docker Deployment

1. Create a `.env` file with required environment variables:
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_SETTINGS_MODULE=config.settings_prod
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
REDIS_URL=redis://redis:6379/0
```

2. Build and start the containers:
```bash
docker-compose up --build
```

## API Documentation

### Authentication

The API currently doesn't require authentication as specified in the requirements.

### Rate Limiting

- Anonymous users: 100 requests per minute
- Study sessions: 30 requests per minute
- Word reviews: 60 requests per minute

### Dashboard Endpoints

#### GET /api/dashboard/last_study_session
Returns information about the most recent study session.

Response:
```json
{
  "id": 123,
  "group_id": 456,
  "created_at": "2025-02-08T17:20:23-05:00",
  "study_activity_id": 789,
  "group_name": "Basic Greetings"
}
```

#### GET /api/dashboard/study_progress
Returns study progress statistics.

Response:
```json
{
  "total_words_studied": 3,
  "total_available_words": 124
}
```

#### GET /api/dashboard/quick-stats
Returns quick overview statistics.

Response:
```json
{
  "success_rate": 80.0,
  "total_study_sessions": 4,
  "total_active_groups": 3,
  "study_streak_days": 4
}
```

### Word Management

#### GET /api/words
List all vocabulary words (paginated).

Response:
```json
{
  "items": [
    {
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

#### GET /api/words/:id
Get details of a specific word.

Response:
```json
{
  "urdu": "سلام",
  "urdlish": "salaam",
  "english": "hello",
  "stats": {
    "correct_count": 5,
    "wrong_count": 2
  },
  "groups": [
    {
      "id": 1,
      "name": "Basic Greetings"
    }
  ]
}
```

### Group Management

#### GET /api/groups
List all vocabulary groups (paginated).

Response:
```json
{
  "items": [
    {
      "id": 1,
      "name": "Basic Greetings",
      "word_count": 20
    }
  ],
  "pagination": {
    "current_page": 1,
    "total_pages": 1,
    "total_items": 10,
    "items_per_page": 100
  }
}
```

### Study Sessions

#### POST /api/study_activities
Start a new study session.

Request:
```json
{
  "group_id": 123,
  "study_activity_id": 456
}
```

Response:
```json
{
  "id": 124,
  "group_id": 123
}
```

#### POST /api/study_sessions/:id/words/:word_id/review
Record a word review result.

Request:
```json
{
  "correct": true
}
```

Response:
```json
{
  "success": true,
  "word_id": 1,
  "study_session_id": 123,
  "correct": true,
  "created_at": "2025-02-08T17:33:07-05:00"
}
```

### System Management

#### POST /api/reset_history
Reset all study history.

Response:
```json
{
  "success": true,
  "message": "Study history has been reset"
}
```

#### POST /api/full_reset
Reset the entire system.

Response:
```json
{
  "success": true,
  "message": "System has been fully reset"
}
```

## Development Tools

### Available Commands

```bash
# Run tests
python scripts/manage.py test

# Run development server with debug toolbar
DJANGO_SETTINGS_MODULE=config.settings_dev python scripts/manage.py runserver

# Generate API documentation
python scripts/manage.py spectacular --file schema.yml

# Check code style
black .
flake8 .
```

### API Documentation UI

- Swagger UI: `/swagger/`
- ReDoc: `/redoc/`
- OpenAPI Schema: `/api/schema/`

## Monitoring

- Health Check: `/health/`
- Performance Monitoring: Check logs in `/var/log/django/debug.log`
- Query Monitoring: Available in development through Django Debug Toolbar

## License

This project is licensed under the MIT License - see the LICENSE file for details. 