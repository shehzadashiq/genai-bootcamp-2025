# Development Guide

This guide explains how to set up and run the Language Learning Portal backend.

## Prerequisites

1. Install Go 1.21 or later

   ```bash
   # Check your Go version
   go version
   ```

2. Install SQLite3

   ```bash
   # Ubuntu/Debian
   sudo apt-get install sqlite3
   
   # macOS
   brew install sqlite3
   ```

3. Install Mage

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

## Common SQLite commands

```sql
.tables           -- List all tables
.schema words     -- Show schema for words table
.quit            -- Exit SQLite shell
```

## Troubleshooting

1. If the database is corrupted:

   ```bash
   mage initdb
   mage migrate
   mage seed
   ```

2. If port 8080 is in use:

   ```bash
   # Find process using port 8080
   lsof -i :8080
   
   # Kill the process
   kill <PID>
   ```

3. To reset all data:

   ```bash
   curl -X POST http://localhost:8080/api/full_reset
   ```
