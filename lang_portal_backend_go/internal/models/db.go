package models

import (
	"database/sql"
)

type DB struct {
	*sql.DB
}

func NewDB(db *sql.DB) *DB {
	return &DB{db}
}

func NewTestDB() (*DB, error) {
	// Create a temporary SQLite database
	db, err := sql.Open("sqlite3", ":memory:")
	if err != nil {
		return nil, err
	}

	// Create tables
	_, err = db.Exec(`
		CREATE TABLE IF NOT EXISTS words (
			id INTEGER PRIMARY KEY,
			word TEXT NOT NULL,
			translation TEXT NOT NULL,
			pronunciation TEXT,
			example TEXT,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS word_groups (
			id INTEGER PRIMARY KEY,
			name TEXT NOT NULL,
			description TEXT,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP
		);

		CREATE TABLE IF NOT EXISTS words_groups (
			id INTEGER PRIMARY KEY,
			word_id INTEGER,
			group_id INTEGER,
			FOREIGN KEY (word_id) REFERENCES words(id),
			FOREIGN KEY (group_id) REFERENCES word_groups(id)
		);

		CREATE TABLE IF NOT EXISTS study_sessions (
			id INTEGER PRIMARY KEY,
			group_id INTEGER,
			activity_name TEXT,
			group_name TEXT,
			start_time DATETIME,
			end_time DATETIME,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (group_id) REFERENCES word_groups(id)
		);

		CREATE TABLE IF NOT EXISTS word_review_items (
			id INTEGER PRIMARY KEY,
			word_id INTEGER,
			study_session_id INTEGER,
			correct BOOLEAN,
			created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (word_id) REFERENCES words(id),
			FOREIGN KEY (study_session_id) REFERENCES study_sessions(id)
		);
	`)
	if err != nil {
		return nil, err
	}

	// Insert test data
	_, err = db.Exec(`
		INSERT INTO words (id, word, translation, pronunciation, example) VALUES
		(1, 'hello', 'こんにちは', 'konnichiwa', 'Hello, how are you?'),
		(2, 'goodbye', 'さようなら', 'sayounara', 'Goodbye, see you tomorrow.'),
		(3, 'thank you', 'ありがとう', 'arigatou', 'Thank you for your help.');

		INSERT INTO word_groups (id, name, description) VALUES
		(1, 'Beginner Words', 'Basic vocabulary for beginners'),
		(2, 'Intermediate Words', 'Vocabulary for intermediate learners');

		INSERT INTO words_groups (word_id, group_id) VALUES
		(1, 1),
		(2, 1),
		(3, 1),
		(1, 2),
		(2, 2);
	`)
	if err != nil {
		return nil, err
	}

	return &DB{db}, nil
}
