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
