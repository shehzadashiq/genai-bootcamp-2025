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
	fmt.Println("Seeding database...")

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

	// Start a transaction
	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}

	// Import study activities from seed file
	studyActivitiesFile := "db/seeds/study_activities.json"
	if err := importStudyActivities(tx, studyActivitiesFile); err != nil {
		tx.Rollback()
		return fmt.Errorf("failed to import study activities: %v", err)
	}

	// Create default groups
	_, err = tx.Exec(`
		INSERT OR REPLACE INTO groups (name) VALUES 
		('Beginner Words'),
		('Intermediate Words'),
		('Advanced Words')
	`)
	if err != nil {
		tx.Rollback()
		return fmt.Errorf("failed to insert groups: %v", err)
	}

	// Import words from JSON files
	wordFiles := []string{
		"db/seeds/basic_words.json",
		"db/seeds/common_phrases.json",
	}

	// Get the beginner group ID
	var beginnerGroupID int64
	err = tx.QueryRow("SELECT id FROM groups WHERE name = 'Beginner Words'").Scan(&beginnerGroupID)
	if err != nil {
		tx.Rollback()
		return fmt.Errorf("failed to get beginner group ID: %v", err)
	}

	for _, file := range wordFiles {
		if err := importSeedFile(tx, file, beginnerGroupID); err != nil {
			tx.Rollback()
			return fmt.Errorf("failed to import %s: %v", file, err)
		}
	}

	// Commit the transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	fmt.Println("Database seeded successfully")
	return nil
}

func importStudyActivities(tx *sql.Tx, filePath string) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file: %v", err)
	}

	var activities []struct {
		ID           int     `json:"id"`
		Name         string  `json:"name"`
		ThumbnailURL string  `json:"thumbnail_url"`
		Description  string  `json:"description"`
	}
	if err := json.Unmarshal(data, &activities); err != nil {
		return fmt.Errorf("error parsing JSON: %v", err)
	}

	for _, activity := range activities {
		_, err = tx.Exec(`
			INSERT OR REPLACE INTO study_activities (id, name, thumbnail_url, description, created_at)
			VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
		`, activity.ID, activity.Name, activity.ThumbnailURL, activity.Description)
		if err != nil {
			return fmt.Errorf("error inserting activity: %v", err)
		}
	}

	return nil
}

func importSeedFile(tx *sql.Tx, filePath string, groupID int64) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return fmt.Errorf("error reading file: %v", err)
	}

	var words []seedWord
	if err := json.Unmarshal(data, &words); err != nil {
		return fmt.Errorf("error parsing JSON: %v", err)
	}

	for _, word := range words {
		// Insert word
		result, err := tx.Exec(`
			INSERT INTO words (urdu, urdlish, english, parts)
			VALUES (?, ?, ?, ?)
		`, word.Urdu, word.Urdlish, word.English, word.Parts)
		if err != nil {
			return fmt.Errorf("error inserting word: %v", err)
		}

		// Get the word ID
		wordID, err := result.LastInsertId()
		if err != nil {
			return fmt.Errorf("error getting last insert ID: %v", err)
		}

		// Link word to group
		_, err = tx.Exec(`
			INSERT INTO words_groups (word_id, group_id)
			VALUES (?, ?)
		`, wordID, groupID)
		if err != nil {
			return fmt.Errorf("error linking word to group: %v", err)
		}
	}

	return nil
}
