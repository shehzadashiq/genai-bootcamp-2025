package testutil

import (
	"database/sql"
	"testing"

	_ "github.com/mattn/go-sqlite3"
)

// TestDB represents a test database helper
type TestDB struct {
	*sql.DB
	t *testing.T
}

// NewTestDB creates a new test database
func NewTestDB(t *testing.T) *TestDB {
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		t.Fatalf("Failed to open test db: %v", err)
	}

	// Configure connection pool for in-memory database
	db.SetMaxOpenConns(1)
	db.SetMaxIdleConns(1)
	db.SetConnMaxLifetime(0)

	// Enable foreign keys
	if _, err := db.Exec("PRAGMA foreign_keys = ON"); err != nil {
		t.Fatalf("Failed to enable foreign keys: %v", err)
	}

	// Run migrations
	migrations := []string{
		`CREATE TABLE IF NOT EXISTS words (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			urdu TEXT NOT NULL,
			urdlish TEXT NOT NULL,
			english TEXT NOT NULL,
			parts TEXT
		);`,
		`CREATE TABLE IF NOT EXISTS groups (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL
		);`,
		`CREATE TABLE IF NOT EXISTS study_activities (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			thumbnail_url TEXT,
			description TEXT,
			group_id INTEGER,
			created_at DATETIME,
			FOREIGN KEY (group_id) REFERENCES groups(id)
		);`,
		`CREATE TABLE IF NOT EXISTS words_groups (
			word_id INTEGER NOT NULL,
			group_id INTEGER NOT NULL,
			FOREIGN KEY (word_id) REFERENCES words(id),
			FOREIGN KEY (group_id) REFERENCES groups(id),
			PRIMARY KEY (word_id, group_id)
		);`,
		`CREATE TABLE IF NOT EXISTS study_sessions (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			group_id INTEGER NOT NULL,
			created_at DATETIME NOT NULL,
			study_activity_id INTEGER NOT NULL,
			FOREIGN KEY (group_id) REFERENCES groups(id),
			FOREIGN KEY (study_activity_id) REFERENCES study_activities(id)
		);`,
		`CREATE TABLE IF NOT EXISTS word_review_items (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			word_id INTEGER NOT NULL,
			study_session_id INTEGER NOT NULL,
			correct BOOLEAN NOT NULL,
			created_at DATETIME NOT NULL,
			FOREIGN KEY (word_id) REFERENCES words(id),
			FOREIGN KEY (study_session_id) REFERENCES study_sessions(id)
		);`,
	}

	for _, migration := range migrations {
		if _, err := db.Exec(migration); err != nil {
			t.Fatalf("Failed to run migration: %v", err)
		}
	}

	return &TestDB{DB: db, t: t}
}

// Seed adds test data to the database
func (db *TestDB) Seed() {
	seedData := []string{
		// First, insert groups
		`INSERT INTO groups (name) VALUES ('Test Group');`,

		// Then, insert words
		`INSERT INTO words (urdu, urdlish, english) VALUES 
			('سلام', 'salaam', 'hello'),
			('شکریہ', 'shukriya', 'thank you');`,

		// Then, link words to groups
		`INSERT INTO words_groups (word_id, group_id) VALUES (1, 1), (2, 1);`,

		// Then, create study activities
		`INSERT INTO study_activities (name, description, created_at) VALUES 
			('Vocabulary Quiz', 'Practice your vocabulary', datetime('now'));`,

		// Then, create study sessions
		`INSERT INTO study_sessions (group_id, created_at, study_activity_id) 
			VALUES (1, datetime('now'), 1);`,

		// Finally, add word reviews
		`INSERT INTO word_review_items (word_id, study_session_id, correct, created_at)
			VALUES (1, 1, true, datetime('now'));`,
	}

	// Execute each statement separately to catch specific errors
	for _, sql := range seedData {
		if _, err := db.Exec(sql); err != nil {
			db.t.Fatalf("Failed to seed data with statement '%s': %v", sql, err)
		}
	}
}

// Cleanup closes the database and removes any temporary files
func (db *TestDB) Cleanup() {
	if err := db.Close(); err != nil {
		db.t.Errorf("Failed to close test db: %v", err)
	}
} 