# Language Learning Portal Backend

A Go-based backend service for managing vocabulary learning and study sessions.

## Table of Contents

- [Language Learning Portal Backend](#language-learning-portal-backend)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Technical Specifications](#technical-specifications)
  - [Features](#features)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Development](#development)
    - [Start the server](#start-the-server)
    - [Available Commands](#available-commands)
    - [Testing the API](#testing-the-api)
    - [Development Database](#development-database)
    - [Database Migrations](#database-migrations)
    - [Common SQLite Commands](#common-sqlite-commands)
  - [Project Structure](#project-structure)
  - [Database](#database)
    - [Schema](#schema)
      - [words](#words)
      - [groups](#groups)
      - [words\_groups](#words_groups)
    - [Seeding](#seeding)
  - [API Documentation](#api-documentation)
    - [Authentication](#authentication)
    - [Response Format](#response-format)
    - [Error Responses](#error-responses)
    - [Pagination](#pagination)
    - [Key Endpoints](#key-endpoints)
      - [Dashboard](#dashboard)
      - [Study Activities](#study-activities)
      - [Words](#words-1)
      - [Groups](#groups-1)
      - [Study Sessions](#study-sessions)
      - [System](#system)
  - [Testing](#testing)
    - [Service Tests](#service-tests)
    - [Handler Tests](#handler-tests)
    - [Integration Tests](#integration-tests)
    - [Coverage](#coverage)
  - [Troubleshooting](#troubleshooting)
  - [Testing Framework Troubleshooting](#testing-framework-troubleshooting)
    - [SQLite In-Memory Database Concurrency Issues](#sqlite-in-memory-database-concurrency-issues)
  - [References](#references)

## Overview

The Language Learning Portal backend provides

- Inventory of possible vocabulary
- Learning record store (LRS) for practice tracking
- Unified launchpad for learning apps

## Technical Specifications

- **Language**: Go 1.21+
- **Database**: SQLite3
- **Framework**: Gin
- **Task Runner**: Mage
- **Response Format**: JSON
- **Authentication**: None (single user)
- **Pagination**: 100 items per page

## Features

- Vocabulary management with groups
- Study session tracking
- Progress monitoring
- Word review history
- Dashboard with statistics

## Prerequisites

Note: Make sure to set up your environment variables before running the application:

```bash
# Required for SQLite
export CGO_ENABLED=1  # Linux/macOS
$env:CGO_ENABLED=1   # Windows PowerShell

# Optional: Set custom port
export PORT=8080     # Default is 8080
```

1. Install Go 1.21 or later

    Windows:
    - Download installer from [Go Downloads](https://golang.org/dl/)
    - Run the installer
    - Verify installation: `go version`
    - Add to PATH if needed: `C:\Go\bin`

    macOS:

    ```bash
    brew install go
    go version
    ```

    Ubuntu/Debian:

    ```bash
    wget https://golang.org/dl/go1.21.linux-amd64.tar.gz
    sudo tar -C /usr/local -xzf go1.21.linux-amd64.tar.gz
    echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.profile
    source ~/.profile
    go version
    ```

2. Install SQLite3

   Windows:
   - Download from [SQLite Download Page](https://www.sqlite.org/download.html)
   - Extract sqlite3.exe to PATH

   macOS:
   - `brew install sqlite3`

   Ubuntu/Debian:
   - `sudo apt-get install sqlite3`

3. Install GCC (required for CGO)

   Windows:
   - Install [MSYS2](https://www.msys2.org/)
   - Run `pacman -S mingw-w64-x86_64-gcc`
   - Add `C:\msys64\mingw64\bin` to PATH

   macOS:
   - `xcode-select --install`

   Ubuntu/Debian:
   - `sudo apt-get install build-essential`

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

## Setup

1. Clone and navigate:

   ```bash
   cd lang_portal/backend_go
   ```

2. Install dependencies:

   ```bash
   go mod download
   go mod tidy
   ```

3. Initialize database:

   ```bash
   mage initdb
   mage migrate
   mage seed
   ```

## Development

### Start the server

- `go run cmd/server/main.go`

Server runs at [http://localhost:8080](http://localhost:8080)

### Available Commands

- `mage initdb` - Creates database
- `mage migrate` - Runs migrations
- `mage seed` - Imports sample data

### Testing the API

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

### Development Database

The SQLite database is stored in `words.db` in the project root. You can inspect it using:

```bash
sqlite3 words.db
```

To verify installation:

```bash
sqlite3 --version
```

### Database Migrations

The database schema is managed through migrations in `db/migrations/`. Each migration file contains SQL statements to create or modify tables.

To apply migrations:

```bash
mage migrate
```

To verify migrations:

```sql
.schema           -- Show all table schemas
SELECT * FROM sqlite_master WHERE type='table';  -- List all tables
```

### Common SQLite Commands

```sql
.tables           -- List all tables
.schema words     -- Show schema for words table
.quit            -- Exit SQLite shell
```

## Project Structure

```text
backend_go/
├── cmd/server/      # Application entry point
├── internal/        # Internal packages
│   ├── models/      # Data structures
│   ├── handlers/    # HTTP handlers
│   ├── service/     # Business logic
│   └── middleware/  # HTTP middleware
└── db/             # Database files
    ├── migrations/  # SQL migrations
    └── seeds/       # Sample data
```

## Database

### Schema

- `words` - Vocabulary entries
- `groups` - Word groupings
- `words_groups` - Many-to-many relationships
- `study_activities` - Study activity types
- `study_sessions` - Study session records
- `word_review_items` - Word review history

#### words

```sql
CREATE TABLE words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urdu TEXT NOT NULL,
    urdlish TEXT NOT NULL,
    english TEXT NOT NULL,
    parts TEXT
);
```

#### groups

```sql
CREATE TABLE groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
);
```

#### words_groups

```sql
CREATE TABLE words_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id INTEGER NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY (word_id) REFERENCES words(id),
    FOREIGN KEY (group_id) REFERENCES groups(id)
);
```

### Seeding

Add new words via JSON files in `db/seeds/`

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

## API Documentation

All endpoints return JSON and are prefixed with `/api`. For detailed documentation, see [API.md](API.md).

### Authentication

This API does not require authentication as it's designed for single-user use.

### Response Format

All responses follow this structure:

```json
{
    "data": {}, // Response data
    "meta": {}, // Additional metadata
    "pagination": {} // For paginated responses
}
```

### Error Responses

Error responses follow this format:

```json
{
    "error": "Error message description",
    "code": "ERROR_CODE"
}
```

Common status codes:

- 400 - Bad Request (invalid input)
- 404 - Not Found
- 500 - Internal Server Error

### Pagination

List endpoints support pagination with these query parameters:

- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 100)

Response includes pagination metadata:

```json
{
    "pagination": {
        "current_page": 1,
        "total_pages": 5,
        "total_items": 50,
        "items_per_page": 100
    }
}
```

### Key Endpoints

#### Dashboard

- `GET /dashboard/last_study_session` - Latest study session
- `GET /dashboard/study_progress` - Overall progress
- `GET /dashboard/quick-stats` - Dashboard statistics

```json
{
    "total_words_studied": 50,
    "total_available_words": 100
}
```

#### Study Activities

- `GET /study_activities/:id` - Activity details

```json
{
    "id": 1,
    "name": "Vocabulary Quiz",
    "thumbnail_url": "https://example.com/thumbnails/1.jpg",
    "description": "Practice your vocabulary with flashcards"
}
```

#### Words

- `GET /words` - List all words

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

#### Groups

- `GET /groups` - List all groups
- `GET /groups/:id` - Group details
- `GET /groups/:id/words` - Words in group
- `GET /groups/:id/study_sessions` - Group study sessions

#### Study Sessions

- `GET /study_sessions` - List all sessions
- `GET /study_sessions/:id` - Session details
- `GET /study_sessions/:id/words` - Words reviewed in session
- `POST /study_sessions/:id/words/:word_id/review` - Record word review

#### System

- `POST /reset_history` - Reset study history
- `POST /full_reset` - Reset entire system

## Testing

### Service Tests

```bash
go test ./internal/service -v
```

Tests business logic layer

### Handler Tests

```bash
go test ./internal/handlers -v
```

Tests HTTP endpoints

### Integration Tests

```bash
go test ./... -v        # All tests
go test ./... -short    # Skip integration
```

### Coverage

```bash
go test ./... -cover
```

## Troubleshooting

1. CGO Issues:

   ```bash
   export CGO_ENABLED=1
   go mod tidy
   ```

2. Database Issues:

    ```bash
    mage initdb
    mage migrate
    mage seed
    ```

3. Port Conflicts:

    Windows:

    ```powershell
    netstat -ano | findstr :8080
    taskkill /PID <PID> /F
    ```

    Linux/macOS:

    ```bash
    lsof -i :8080
    kill <PID>
    ```

4. Reset Data:

    ```bash
    curl -X POST http://localhost:8080/api/full_reset
    ```

## Testing Framework Troubleshooting

### SQLite In-Memory Database Concurrency Issues

When running concurrent tests with SQLite in-memory databases, you may encounter these issues:
- "no such table" errors
- Missing data between operations
- Inconsistent record counts

**Root Cause:**
SQLite in-memory databases create separate databases for each connection. In concurrent tests, goroutines may create new connections, resulting in isolated databases.

**Solution:**

1. Configure the connection pool to use a single connection

```go
db.SetMaxOpenConns(1)
db.SetMaxIdleConns(1)
db.SetConnMaxLifetime(0)
```

2. Add mutex synchronization for concurrent operations

```go
var mu sync.Mutex

// In concurrent operations:
mu.Lock()
_, err := svc.ReviewWord(sessionID, wordID, true)
mu.Unlock()
```

3. Use channels for error handling in goroutines:

```go
errChan := make(chan error, operationCount)
go func() {
    if err := operation(); err != nil {
        errChan <- err
    }
}()

// Check errors after operations complete
for err := range errChan {
    t.Errorf("Operation failed: %v", err)
}
```

**Why This Works:**

- Single connection ensures all operations use the same in-memory database
- Mutex prevents race conditions during concurrent database access
- Error channel allows proper error reporting from goroutines

**Example:**
See `TestConcurrentWordReviews` in `internal/service/concurrent_test.go` for a complete implementation.

## References

Because sometimes AI does not have all the answers. There is no alternative to good old troubleshooting.

- [How to Install GCC and GDB on Windows Using MSYS2 — Tutorial](https://sajidifti.medium.com/how-to-install-gcc-and-gdb-on-windows-using-msys2-tutorial-0fceb7e66454)
