# Development Guide

This guide explains how to set up and run the Language Learning Portal backend.

## Prerequisites

1. Install Go 1.21 or later

   ```bash
   # Check your Go version
   go version
   ```

2. Install SQLite3

   Windows:
   - Download the SQLite tools from [SQLite Download Page](https://www.sqlite.org/download.html)
   - Download the "Precompiled Binaries for Windows" bundle
   - Extract sqlite3.exe to a folder in your PATH
   - Verify installation: `sqlite3 --version`

   macOS:
   - brew install sqlite3

   Ubuntu/Debian:
   - sudo apt-get install sqlite3

3. Install GCC (required for CGO)

   Windows:
   - Download and install [MSYS2](https://www.msys2.org/)
   - Open MSYS2 and run `pacman -S mingw-w64-x86_64-gcc`
   - Add `C:\msys64\mingw64\bin` to your system PATH

   macOS:
   - xcode-select --install

   Ubuntu/Debian:
   - sudo apt-get install build-essential

4. Enable CGO

   ```powershell
   # Windows (PowerShell)
   $env:CGO_ENABLED=1
   
   # Linux/macOS
   export CGO_ENABLED=1
   ```

5. Install Mage

   ```bash
   go install github.com/magefile/mage@latest
   ```

## First-Time Setup

1. Clone the repository and navigate to the backend directory:

   ```bash
   cd lang_portal/backend_go
   ```

2. Install dependencies:

   ```bash
   go mod download
   go mod tidy
   ```

3. Initialize the database:

   ```bash
   mage initdb
   ```

4. Run database migrations:

   ```bash
   mage migrate
   ```

5. Import sample data:

   ```bash
   mage seed
   ```

## Running the Server

Start the development server:

```bash
go run cmd/server/main.go
```

The server will start on [http://localhost:8080](http://localhost:8080)

## Development Tasks

Common development tasks can be run using Mage:

```bash
# Build and run the server
mage run

# Run database migrations
mage migrate

# Reset database and run migrations
mage reset

# Run tests
mage test

# Run tests with coverage
mage testWithCoverage
```

## API Testing

You can test the API endpoints using curl or any HTTP client. Here are some example requests:

### Start a Vocabulary Quiz

```bash
curl -X POST http://localhost:8080/api/vocabulary-quiz/start \
  -H "Content-Type: application/json" \
  -d '{"group_id": 1, "word_count": 10}'
```

### Get Quiz Words

```bash
curl http://localhost:8080/api/vocabulary-quiz/words/1
```

### Submit Quiz Answer

```bash
curl -X POST http://localhost:8080/api/vocabulary-quiz/answer \
  -H "Content-Type: application/json" \
  -d '{"session_id": 1, "word_id": 1, "answer": "hello", "correct": true}'
```

### Get Quiz Score

```bash
curl http://localhost:8080/api/vocabulary-quiz/score/1
```

### Get Study Progress

```bash
curl http://localhost:8080/api/dashboard/study_progress
```

## Available Mage Commands

- `mage initdb` - Creates a new SQLite database
- `mage migrate` - Runs all pending migrations
- `mage seed` - Imports sample data
- `mage -l` - Lists all available mage commands

## Testing the API

You can test the API using curl:

```bash
# Get dashboard stats
curl http://localhost:8080/api/dashboard/quick-stats

# Get list of words
curl http://localhost:8080/api/words?page=1

# Create a study session
curl -X POST http://localhost:8080/api/study_activities \
  -H "Content-Type: application/json" \
  -d '{"group_id": 1, "study_activity_id": 1}'
```

## Development Database

The SQLite database is stored in `words.db` in the project root. You can inspect it using:

```bash
sqlite3 words.db
```

## Database Management

### View Database Content

```bash
# Open SQLite shell
sqlite3 words.db

# Show tables
.tables

# Show schema for a table
.schema words
.schema study_sessions
.schema word_review_items

# Query data
SELECT * FROM words LIMIT 5;
SELECT * FROM study_sessions ORDER BY start_time DESC LIMIT 5;
SELECT * FROM word_review_items WHERE session_id = 1;
```

### Reset Database

To reset the database and start fresh:

```bash
# Delete existing database
rm words.db*

# Run migrations
mage migrate

# Seed initial data
mage seed
```

## Common SQLite commands

```sql
.tables           -- List all tables
.schema words     -- Show schema for words table
.quit            -- Exit SQLite shell
```

## Database Seeding

The database is seeded with sample data from JSON files in `db/seeds/`:

- `common_phrases.json` - Basic conversational phrases
- `basic_words.json` - Common vocabulary words

### To add new seed data

1. Create a new JSON file in `db/seeds/`
2. Follow the format:

   ```json
   [
     {
       "urdu": "سلام",
       "urdlish": "salaam",
       "english": "hello",
       "parts": {
         "type": "greeting"
       }
     }
   ]
   ```

3. Run `mage seed` to import the data

## Database Schema

The database includes these main tables:

- `words` - Vocabulary entries
- `groups` - Word groupings (e.g., "Common Phrases")
- `words_groups` - Many-to-many relationship between words and groups
- `study_activities` - Types of study activities
- `study_sessions` - Records of study sessions
- `word_review_items` - Individual word reviews during sessions

## Troubleshooting

1. If you get "go-sqlite3 requires cgo to work":

   ```powershell
   # Windows (PowerShell)
   $env:CGO_ENABLED=1
   
   # Linux/macOS
   export CGO_ENABLED=1
   
   # Then rebuild and run
   go mod tidy
   mage migrate
   ```

2. If the database is corrupted:

   ```powershell
   mage initdb
   mage migrate
   mage seed
   ```

3. If port 8080 is in use:

   Windows

   ```powershell
   # Find process using port 8080
   netstat -ano | findstr :8080
   
   # Kill the process (replace PID with the number from above)
   taskkill /PID <PID> /F
   ```

   Linux/macOS:

   ```bash
   # Find process using port 8080
   lsof -i :8080
   
   # Kill the process
   kill <PID>
   ```

4. To reset all data:

   ```bash
   curl -X POST http://localhost:8080/api/full_reset
   ```

## Common Issues

### Database Locked

If you see "database is locked" errors:

1. Make sure you don't have the database open in another program
2. Try closing and reopening the database connection
3. If persists, delete the .db-shm and .db-wal files

### CGO Issues

If you see CGO-related errors:

1. Ensure CGO is enabled: `set CGO_ENABLED=1` (Windows) or `export CGO_ENABLED=1` (Unix)
2. Check that GCC is installed and in your PATH
3. On Windows, verify MSYS2 is properly installed
