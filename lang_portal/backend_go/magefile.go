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
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return fmt.Errorf("failed to create database: %v", err)
	}
	defer db.Close()

	fmt.Println("Database created successfully")
	return nil
}

// Migrate runs all database migrations
func Migrate() error {
	fmt.Println("Running migrations...")
	
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return fmt.Errorf("failed to open database: %v", err)
	}
	defer db.Close()

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
	
	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return fmt.Errorf("failed to open database: %v", err)
	}
	defer db.Close()

	// Add default study activities
	activities := []struct {
		name, desc string
	}{
		{"Vocabulary Quiz", "Practice your vocabulary with flashcards"},
		{"Word Match", "Match words with their meanings"},
		{"Sentence Builder", "Create sentences using learned words"},
	}

	for _, a := range activities {
		_, err := db.Exec(`
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
		if err := importSeedFile(db, file, groupName); err != nil {
			return fmt.Errorf("error importing %s: %v", file, err)
		}
	}

	fmt.Println("Sample data imported successfully")
	return nil
}

func importSeedFile(db *sql.DB, filePath, groupName string) error {
	data, err := ioutil.ReadFile(filePath)
	if err != nil {
		return err
	}

	var words []seedWord
	if err := json.Unmarshal(data, &words); err != nil {
		return err
	}

	tx, err := db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

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

	return tx.Commit()
} 