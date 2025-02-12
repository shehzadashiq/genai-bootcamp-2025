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

// InitDB initializes the SQLite database
func InitDB() error {
	if _, err := os.Stat("words.db"); err == nil {
		return fmt.Errorf("database already exists")
	}

	db, err := sql.Open("sqlite3", "words.db")
	if err != nil {
		return err
	}
	defer db.Close()

	return nil
}

// Migrate runs all pending migrations
func Migrate() error {
	db, err := sql.Open("sqlite3", "words.db")
	if err != nil {
		return err
	}
	defer db.Close()

	files, err := filepath.Glob("db/migrations/*.sql")
	if err != nil {
		return err
	}

	sort.Strings(files)

	for _, file := range files {
		content, err := os.ReadFile(file)
		if err != nil {
			return err
		}

		statements := strings.Split(string(content), ";")
		for _, stmt := range statements {
			if strings.TrimSpace(stmt) != "" {
				if _, err := db.Exec(stmt); err != nil {
					return fmt.Errorf("error executing %s: %v", file, err)
				}
			}
		}
	}

	return nil
}

// Seed imports data from JSON files
func Seed() error {
	db, err := sql.Open("sqlite3", "words.db")
	if err != nil {
		return err
	}
	defer db.Close()

	files, err := filepath.Glob("db/seeds/*.json")
	if err != nil {
		return err
	}

	for _, file := range files {
		// Get group name from filename
		base := filepath.Base(file)
		groupName := strings.TrimSuffix(base, filepath.Ext(base))
		
		if err := importSeedFile(db, file, groupName); err != nil {
			return fmt.Errorf("error importing %s: %v", file, err)
		}
	}

	return nil
}

type seedWord struct {
	Urdu    string          `json:"urdu"`
	Urdlish string          `json:"urdlish"`
	English string          `json:"english"`
	Parts   json.RawMessage `json:"parts"`
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