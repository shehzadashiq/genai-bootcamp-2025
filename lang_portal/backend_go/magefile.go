//go:build mage

package main

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"sort"
	"strings"

	_ "github.com/mattn/go-sqlite3"
)

const dbPath = "words.db"

type seedWord struct {
	Urdu    string          `json:"urdu"`
	Urdlish string          `json:"urdlish"`
	English string          `json:"english"`
	Parts   json.RawMessage `json:"parts"`
}

// InitDB creates a new SQLite database
func InitDB() error {
	fmt.Println("Creating new database...")

	// Remove existing database if it exists
	if _, err := os.Stat(dbPath); err == nil {
		if err := os.Remove(dbPath); err != nil {
			return fmt.Errorf("failed to remove existing database: %v", err)
		}
	}

	// Create new database file
	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000&_fk=true&cache=shared")
	if err != nil {
		return fmt.Errorf("failed to create database: %v", err)
	}
	defer db.Close()

	// Enable WAL mode and set busy timeout
	if _, err := db.Exec("PRAGMA journal_mode=WAL"); err != nil {
		return fmt.Errorf("failed to set journal mode: %v", err)
	}
	if _, err := db.Exec("PRAGMA busy_timeout=5000"); err != nil {
		return fmt.Errorf("failed to set busy timeout: %v", err)
	}

	fmt.Println("Database created successfully")
	return nil
}

// Migrate runs all database migrations
func Migrate() error {
	fmt.Println("Running migrations...")

	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000&_fk=true&cache=shared")
	if err != nil {
		return fmt.Errorf("failed to open database: %v", err)
	}
	defer db.Close()

	// Enable WAL mode and set busy timeout
	if _, err := db.Exec("PRAGMA journal_mode=WAL"); err != nil {
		return fmt.Errorf("failed to set journal mode: %v", err)
	}
	if _, err := db.Exec("PRAGMA busy_timeout=5000"); err != nil {
		return fmt.Errorf("failed to set busy timeout: %v", err)
	}

	// Read migrations from db/migrations directory
	files, err := filepath.Glob("db/migrations/*.sql")
	if err != nil {
		return fmt.Errorf("failed to read migrations: %v", err)
	}

	// Sort files to ensure consistent order
	sort.Strings(files)

	for _, file := range files {
		fmt.Printf("Running migration %s...\n", filepath.Base(file))

		data, err := ioutil.ReadFile(file)
		if err != nil {
			return fmt.Errorf("error reading %s: %v", file, err)
		}

		// Split file into separate statements
		sqlContent := strings.TrimSpace(string(data))
		statements := strings.Split(sqlContent, ";")

		for _, stmt := range statements {
			stmt = strings.TrimSpace(stmt)
			if stmt == "" {
				continue
			}

			// Add back the semicolon
			if !strings.HasSuffix(stmt, ";") {
				stmt += ";"
			}

			if _, err := db.Exec(stmt); err != nil {
				return fmt.Errorf("error executing %s: %v", file, err)
			}
		}
	}

	fmt.Println("Migrations completed successfully")
	return nil
}

// Seed imports sample data
func Seed() error {
	fmt.Println("Importing sample data...")

	db, err := sql.Open("sqlite3", dbPath+"?_journal=WAL&_timeout=5000&_fk=true&cache=shared")
	if err != nil {
		return fmt.Errorf("failed to open database: %v", err)
	}
	defer db.Close()

	// Enable WAL mode and set busy timeout
	if _, err := db.Exec("PRAGMA journal_mode=WAL"); err != nil {
		return fmt.Errorf("failed to set journal mode: %v", err)
	}
	if _, err := db.Exec("PRAGMA busy_timeout=5000"); err != nil {
		return fmt.Errorf("failed to set busy timeout: %v", err)
	}

	// Start transaction
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// Add default study activities
	activities := []struct {
		name, desc string
	}{
		{"Vocabulary Quiz", "Practice your vocabulary with flashcards"},
		{"Word Match", "Match words with their meanings"},
		{"Sentence Builder", "Create sentences using learned words"},
	}

	for _, a := range activities {
		_, err := tx.Exec(`
			INSERT INTO study_activities (name, description)
			VALUES (?, ?)
		`, a.name, a.desc)
		if err != nil {
			return fmt.Errorf("failed to insert activity: %v", err)
		}
	}

	// Import seed data from JSON files
	seedFiles := map[string]string{
		"db/seeds/common_phrases.json": "Common Phrases",
		"db/seeds/basic_words.json":    "Basic Words",
	}

	for file, groupName := range seedFiles {
		if err := importSeedFile(tx, file, groupName); err != nil {
			return fmt.Errorf("error importing %s: %v", file, err)
		}
	}

	// Add sample study sessions
	// First get a group ID
	var groupID int64
	err = tx.QueryRow("SELECT id FROM groups LIMIT 1").Scan(&groupID)
	if err != nil {
		return fmt.Errorf("failed to get group ID: %v", err)
	}

	// Get study activity IDs
	activityRows, err := tx.Query("SELECT id FROM study_activities")
	if err != nil {
		return fmt.Errorf("failed to get activity IDs: %v", err)
	}

	var activityIDs []int64
	for activityRows.Next() {
		var id int64
		if err := activityRows.Scan(&id); err != nil {
			activityRows.Close()
			return fmt.Errorf("failed to scan activity ID: %v", err)
		}
		activityIDs = append(activityIDs, id)
	}
	activityRows.Close()
	if err = activityRows.Err(); err != nil {
		return fmt.Errorf("error iterating activity rows: %v", err)
	}

	// Create some study sessions
	for i := 0; i < 5; i++ {
		activityID := activityIDs[i%len(activityIDs)]
		_, err := tx.Exec(`
			INSERT INTO study_sessions (study_activity_id, group_id, created_at)
			VALUES (?, ?, datetime('now', ?))
		`, activityID, groupID, fmt.Sprintf("-%d days", i))
		if err != nil {
			return fmt.Errorf("failed to insert study session: %v", err)
		}
	}

	// Add some word reviews for each session
	var wordIDs []int64
	wordRows, err := tx.Query("SELECT id FROM words")
	if err != nil {
		return fmt.Errorf("failed to get word IDs: %v", err)
	}

	for wordRows.Next() {
		var id int64
		if err := wordRows.Scan(&id); err != nil {
			wordRows.Close()
			return fmt.Errorf("failed to scan word ID: %v", err)
		}
		wordIDs = append(wordIDs, id)
	}
	wordRows.Close()
	if err = wordRows.Err(); err != nil {
		return fmt.Errorf("error iterating word rows: %v", err)
	}

	sessionRows, err := tx.Query("SELECT id FROM study_sessions")
	if err != nil {
		return fmt.Errorf("failed to get session IDs: %v", err)
	}

	for sessionRows.Next() {
		var sessionID int64
		if err := sessionRows.Scan(&sessionID); err != nil {
			sessionRows.Close()
			return fmt.Errorf("failed to scan session ID: %v", err)
		}

		// Add word reviews for each session
		for _, wordID := range wordIDs {
			_, err := tx.Exec(`
				INSERT INTO word_review_items (study_session_id, word_id, correct, created_at)
				VALUES (?, ?, ?, datetime('now'))
			`, sessionID, wordID, true)
			if err != nil {
				sessionRows.Close()
				return fmt.Errorf("failed to insert word review: %v", err)
			}
		}
	}
	sessionRows.Close()
	if err = sessionRows.Err(); err != nil {
		return fmt.Errorf("error iterating session rows: %v", err)
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	fmt.Println("Sample data imported successfully")
	return nil
}

func importSeedFile(tx *sql.Tx, filePath, groupName string) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return err
	}

	var words []seedWord
	if err := json.Unmarshal(data, &words); err != nil {
		return err
	}

	// Create group
	result, err := tx.Exec(`
		INSERT INTO groups (name) VALUES (?)
	`, groupName)
	if err != nil {
		return err
	}

	groupID, err := result.LastInsertId()
	if err != nil {
		return err
	}

	// Insert words and create word-group associations
	for _, word := range words {
		result, err := tx.Exec(`
			INSERT INTO words (urdu, urdlish, english, parts)
			VALUES (?, ?, ?, ?)
		`, word.Urdu, word.Urdlish, word.English, word.Parts)
		if err != nil {
			return err
		}

		wordID, err := result.LastInsertId()
		if err != nil {
			return err
		}

		_, err = tx.Exec(`
			INSERT INTO words_groups (word_id, group_id)
			VALUES (?, ?)
		`, wordID, groupID)
		if err != nil {
			return err
		}
	}

	return nil
}
