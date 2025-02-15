package seeder

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"io"
	"lang_portal/internal/models"
	"os"
	"path/filepath"
)

// Seeder handles database seeding operations
type Seeder struct {
	db *models.DB
}

// NewSeeder creates a new seeder instance
func NewSeeder(db *models.DB) *Seeder {
	return &Seeder{db: db}
}

// SeedFromJSON reads JSON files from a directory and seeds the database
func (s *Seeder) SeedFromJSON(seedDir string) error {
	// Seed study activities
	if err := s.seedStudyActivities(filepath.Join(seedDir, "study_activities.json")); err != nil {
		return fmt.Errorf("failed to seed study activities: %v", err)
	}

	// Seed word groups and words
	if err := s.seedWordGroups(filepath.Join(seedDir, "word_groups.json")); err != nil {
		return fmt.Errorf("failed to seed word groups: %v", err)
	}

	return nil
}

// seedStudyActivities seeds study activities from a JSON file
func (s *Seeder) seedStudyActivities(filePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file: %v", err)
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return fmt.Errorf("failed to read file: %v", err)
	}

	var activities []models.StudyActivity
	if err := json.Unmarshal(data, &activities); err != nil {
		return fmt.Errorf("failed to parse JSON: %v", err)
	}

	// Begin transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	// Clear existing study activities
	_, err = tx.Exec("DELETE FROM study_activities")
	if err != nil {
		return fmt.Errorf("failed to clear study activities: %v", err)
	}

	// Insert new study activities
	stmt, err := tx.Prepare(`
		INSERT INTO study_activities (id, name, url, thumbnail_url, description)
		VALUES (?, ?, ?, ?, ?)
	`)
	if err != nil {
		return fmt.Errorf("failed to prepare statement: %v", err)
	}
	defer stmt.Close()

	for _, activity := range activities {
		_, err = stmt.Exec(
			activity.ID,
			activity.Name,
			activity.URL,
			activity.ThumbnailURL,
			activity.Description,
		)
		if err != nil {
			return fmt.Errorf("failed to insert study activity: %v", err)
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	return nil
}

// seedWordGroups seeds word groups and their words from a JSON file
func (s *Seeder) seedWordGroups(filePath string) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file: %v", err)
	}
	defer file.Close()

	data, err := io.ReadAll(file)
	if err != nil {
		return fmt.Errorf("failed to read file: %v", err)
	}

	type WordGroup struct {
		Name        string `json:"name"`
		Description string `json:"description"`
		Words       []struct {
			Urdu    string `json:"urdu"`
			Urdlish string `json:"urdlish"`
			English string `json:"english"`
		} `json:"words"`
	}

	var groups []WordGroup
	if err := json.Unmarshal(data, &groups); err != nil {
		return fmt.Errorf("failed to parse JSON: %v", err)
	}

	// Begin transaction
	tx, err := s.db.Begin()
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %v", err)
	}
	defer tx.Rollback()

	for _, group := range groups {
		// Get or create group
		var groupID int64
		err := tx.QueryRow(`
			SELECT id FROM groups WHERE name = ?
		`, group.Name).Scan(&groupID)
		if err == sql.ErrNoRows {
			// Insert new group
			result, err := tx.Exec(`
				INSERT INTO groups (name)
				VALUES (?)
			`, group.Name)
			if err != nil {
				return fmt.Errorf("failed to insert group: %v", err)
			}
			groupID, err = result.LastInsertId()
			if err != nil {
				return fmt.Errorf("failed to get group ID: %v", err)
			}
		} else if err != nil {
			return fmt.Errorf("failed to query group: %v", err)
		}

		// Insert words and create word-group associations
		for _, word := range group.Words {
			// Insert word
			result, err := tx.Exec(`
				INSERT INTO words (urdu, urdlish, english)
				VALUES (?, ?, ?)
			`, word.Urdu, word.Urdlish, word.English)
			if err != nil {
				return fmt.Errorf("failed to insert word: %v", err)
			}

			wordID, err := result.LastInsertId()
			if err != nil {
				return fmt.Errorf("failed to get word ID: %v", err)
			}

			// Create word-group association
			_, err = tx.Exec(`
				INSERT INTO words_groups (word_id, group_id)
				VALUES (?, ?)
			`, wordID, groupID)
			if err != nil {
				return fmt.Errorf("failed to associate word with group: %v", err)
			}
		}
	}

	// Commit transaction
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit transaction: %v", err)
	}

	return nil
}
